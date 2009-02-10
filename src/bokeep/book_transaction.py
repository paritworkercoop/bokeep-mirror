from persistent import Persistent
import transaction
from threading import Thread, Condition
from util import \
    ChangeMessageRecievingThread, EntityChangeManager, entitymod

class FinancialTransactionLine(object):
    def __init__(self, amount):
        self.amount = amount

class FinancialTransaction(object):
    def __init__(self, lines):
        self.lines = lines

class BoKeepTransactionNotMappableToFinancialTransaction(Exception):
    pass

class Transaction(Persistent):
    def __init__(self):
        pass

    def get_financial_transactions(self):
        raise BoKeepTransactionNotMappableToFinancialTransaction()

class TransactionDeltaManager(EntityChangeManager):
    def __init__(self, running_thread, entity_identifier):
        EntityChangeManager.__init__(self, running_thread, entity_identifier)
        self.change_list = []
        self.attribute_change_index = {}
        # important value, if there have been no function calls this ensures
        # attribute changes are considerd to occure "after" this
        self.latest_function_call = -1 

def new_transaction_committing_thread(book_set):
    commit_thread = TransactionComittingThread(book_set)
    commit_thread.start()
    return commit_thread

class TransactionComittingThread(ChangeMessageRecievingThread):   
    def __init__(self, book_set):
        ChangeMessageRecievingThread.__init__(self)
        self.book_set = book_set

    def get_arguments_for_exec_procedure(self):
        return ((self.dbroot,), {})

    def new_entity_change_manager(self, entity_identifier):
        return TransactionDeltaManager(self, entity_identifier)

    @entitymod
    def mod_transaction_attr(self, delta, attr_name, attr_value):
        # if the attribute has already been changed, and that change was
        # after the last function call, simply replace the attribute change
        if attr_name in delta.attribute_change_index and \
                delta.attribute_change_index[attr_name] > \
                delta.latest_function_call:
            change_position = delta.attribute_change_index[attr_name]
        # else we create a new attribute change
        else:
            delta.attribute_change_index[attr_name] = change_position = \
                len(delta.change_list)
            delta.change_list.append(None)

        # apply the attribute change, either on top of an old one that
        # we're now ignoring, or as a new one
        delta.change_list[change_position] = (attr_name, attr_value)
        
    @entitymod
    def mod_transaction_with_func(self, delta, function, args, kargs):
        delta.latest_function_call = len(delta.change_list)
        delta.change_list.append( (function, args, kargs) )

    def get_entity_from_identifier(self, entity_identifier):
        (book_name, trans_id) = entity_identifier
        return self.dbroot[book_name].get_transaction(trans_id)
    
    def run(self):
        dbcon = self.book_set.get_new_dbcon()
        self.dbroot = dbcon.root()
        ChangeMessageRecievingThread.run(self)
        dbcon.close()

    def handle_entity_change(self, trans_delta, trans):
        trans_delta.change_list.reverse()
        while len(trans_delta.change_list) > 0:
            change = trans_delta.change_list.pop()
            if len(change) == 3:
                (function_to_call, args, kargs) = change
                function_to_call = getattr(trans, function_to_call)
                function_to_call(*args, **kargs)            
            else:
                assert( len(change) == 2 )
                (attr_name, attr_value) = change
                setattr(trans, attr_name, attr_value)
        trans_delta.attribute_change_index.clear()
        # important value, see comments above
        trans_delta.latest_function_call = -1

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
