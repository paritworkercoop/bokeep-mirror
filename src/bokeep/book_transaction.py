from persistent import Persistent
import transaction
from threading import Thread, Condition
from util import \
    ChangeMessageRecievingThread, EntityChangeManager, entitymod

class Transaction(Persistent):
    def __init__(self):
        pass

class TransactionDeltaManager(EntityChangeManager):
    def __init__(self, running_thread, entity_identifier):
        EntityChangeManager.__init__(self, running_thread, entity_identifier)
        self.attribute_delta = {}
        self.function_calls = []

def new_transaction_committing_thread(book_set):
    commit_thread = TransactionComittingThread(book_set)
    commit_thread.start()
    return commit_thread

class TransactionComittingThread(ChangeMessageRecievingThread):   
    def __init__(self, book_set):
        ChangeMessageRecievingThread.__init__(self)
        self.book_set = book_set

    def new_entity_change_manager(self, entity_identifier):
        return TransactionDeltaManager(self, entity_identifier)

    @entitymod
    def mod_transaction_attr(self, delta, attr_name, attr_value):
        delta.attribute_delta[attr_name] = attr_value
        
    @entitymod
    def mod_transaction_with_func(self, delta, function, args, kargs):
        delta.function_calls.append( (function, args, kargs) )

    def get_entity_from_identifier(self, entity_identifier):
        (book_name, trans_id) = entity_identifier
        return self.dbroot[book_name].get_transaction(trans_id)
    
    def run(self):
        dbcon = self.book_set.get_new_dbcon()
        self.dbroot = dbcon.root()
        ChangeMessageRecievingThread.run(self)
        dbcon.close()

    def handle_entity_change(self, trans_delta, trans):
        for attr, value in \
                trans_delta.attribute_delta.iteritems():
            setattr(trans, attr, value)
        trans_delta.attribute_delta.clear()
                    
        trans_delta.function_calls.reverse()
        while len(trans_delta.function_calls) > 0:
            (function_to_call, args, kargs) = \
                trans_delta.function_calls.pop()
            function_to_call = getattr(trans, function_to_call)
            function_to_call(*args, **kargs)


    def message_block_begin(self):
        transaction.get().commit()

    def message_block_end(self):
        transaction.get().commit()

class TransactionMirror(object):
    """Allows you to change a transaction being handled by a 
    TransactionComittingThread as if you had the transaction itself,
    You can set attributes, and you can call instance mutator functions
    (without access to return values), but you can *NOT* get attributes
    or get the values returned by calling instance methods
    """

    # important, any attributes that are being set must be defined here
    trans_thread = None
    book_name = None
    trans_id = None

    def __init__(self, book_name, trans_id, trans_thread):
        self.trans_thread = trans_thread
        self.book_name = book_name
        self.trans_id = trans_id
    
    def __getattribute__(self, attr_name):
        # if we're looking for an attribute from this instance, return it
        if hasattr(self, attr_name):
            return object.__getattribute__(self, attr_name)
        # else assuming we're fetching an attribute that is an instance mutator
        # function that will modify the transaction
        else:
            def ret_function(*args, **kargs):                
                # note the intentional lack of return
                self.trans_thread.mod_transaction_with_func(
                    (self.book_name, self.trans_id), attr_name, args, kargs)
            return ret_function

    def __setattr__(self, attr_name, value):
        # if we're setting one of the attribute from this class, set it
        # as normal
        if hasattr(self, attr_name):
            object.__setattr__(self, attr_name, value)
        # else set an attribute from the mirror class
        else:
            self.trans_thread.mod_transaction_attr(
                (self.book_name, self.trans_id), attr_name, value)
