from persistent import Persistent
import transaction
from threading import Thread, Condition


class Transaction(Persistent):
    def __init__(self):
        self.backend_dirty = False

class TransactionThreadAction(object):
    pass

class TransactionDeltaBasic(TransactionThreadAction):
    def __init__(self, book_name, trans_id):
        self.book_name = book_name
        self.trans_id = trans_id        

class TransactionDeltaManager(TransactionDeltaBasic):
    def __init__(self, book_name, trans_id):
        TransactionDeltaBasic.__init__(self, book_name, trans_id)
        self.attribute_delta = {}
        self.function_calls = []


class TransactionDeltaEnd(TransactionDeltaBasic):
    pass

class TransactionThreadEnd(TransactionThreadAction):
    pass
        

PRIMARY_DELTA, SECONDARY_DELTA, TRANSACTION = range(3)

def changelock(dec_function):
    def ret_function(self, *args):
        self.change_availible.acquire()
        return_value = dec_function(self, *args)
        self.change_availible.release()
        return return_value
    return ret_function

def transmod(dec_function):
    @changelock
    def ret_function(self, *args):
        delta = self.trans_lookup_dict[
            (args[0], args[1], PRIMARY_DELTA) ]
        return_value = dec_function(self, delta, *args)
        if not delta in self.trans_wait_list:
            self.trans_wait_list.append(delta)
            self.change_availible.notify()
        return return_value
    return ret_function

def waitlistmodify(dec_function):
    @changelock
    def ret_function(self, *args):
        return_value = dec_function(self, *args)
        self.change_availible.notify()
        return return_value
    return ret_function

def new_transaction_committing_thread(book_set):
    commit_thread = TransactionComittingThread(book_set)
    commit_thread.start()
    return commit_thread

class TransactionComittingThread(Thread):   
    def __init__(self, book_set):
        Thread.__init__(self)
        self.trans_wait_list = []
        self.trans_lookup_dict = {}
        self.change_availible = Condition()
        self.book_set = book_set

    @changelock
    def add_transaction(self, book_name, trans_id):
        assert( (book_name, trans_id, PRIMARY_DELTA) not in
                self.trans_lookup_dict )
        for x in (PRIMARY_DELTA, SECONDARY_DELTA):
            self.trans_lookup_dict[(book_name, trans_id, x)] = \
            TransactionDeltaManager(book_name, trans_id)

    @waitlistmodify
    def remove_transaction(self, book_name, trans_id):
        assert( (book_name, trans_id, PRIMARY_DELTA) in
                self.trans_lookup_dict )
        self.trans_wait_list.append( TransactionDeltaEnd(book_name, trans_id) )

    @waitlistmodify
    def request_end_trans_thread(self):
        self.trans_wait_list.append( TransactionThreadEnd() )

    def end_trans_thread(self):
        self.request_end_trans_thread()
        self.join()

    @transmod
    def mod_transaction_attr(
        self, delta, book_name, trans_id, attr_name, attr_value):
        delta.attribute_delta[attr_name] = attr_value
        
    @transmod
    def mod_transaction_with_func(
        self, delta, book_name, trans_id, function, args, kargs):
        delta.function_calls.append(function, args, kargs)

    @changelock
    def get_trans_for_delta(self, delta, dbroot):
        trans_key = (delta.book_name, delta.trans_id, TRANSACTION)
        if not trans_key in self.trans_lookup_dict:
            trans = dbroot[delta.book_name].get_transaction(delta.trans_id)
            self.trans_lookup_dict[trans_key] = trans
        else:
            trans = self.trans_lookup_dict[trans_key]
        return trans

    @changelock
    def remove_delta(self, delta_end):
        for x in (PRIMARY_DELTA, SECONDARY_DELTA, TRANSACTION):
            del self.trans_lookup_dict[
                (delta_end.book_name, delta_end.trans_id, x) ]

    def swap_primary_secondary_deltas(self, delta_list):
        """No lock required, called from a locked context in run()
        """
        for delta in delta_list:
            if isinstance(delta, TransactionDeltaManager):
                delta_keys = [ (delta.book_name, delta.trans_id, x)
                               for x in (PRIMARY_DELTA, SECONDARY_DELTA) ]
                    
                secondary_delta = self.trans_lookup_dict[
                    delta_keys[SECONDARY_DELTA] ]
                self.trans_lookup_dict[ delta_keys[SECONDARY_DELTA] ] = \
                    self.trans_lookup_dict[ delta_keys[PRIMARY_DELTA] ]
                self.trans_lookup_dict[ delta_keys[PRIMARY_DELTA] ] = \
                    secondary_delta        
    
    def run(self):
        dbcon = self.book_set.get_new_dbcon()
        dbroot = dbcon.root()
        run_thread = True
        empty_list = []

        while run_thread:
            self.change_availible.acquire()
            if len(self.trans_wait_list) == 0:
                self.change_availible.wait()
            assert( len(self.trans_wait_list) > 0 )
            
            # lock still acquired [.acquire()] or reacquired [.wait()] here
            # we quickly switch out the waiting list of deltas
            # with the bait of the list of empty deltas,
            # switch the primary and secondary deltas in self.trans_lookup_dict
            # and give up the lock again
            trans_to_handle = self.trans_wait_list
            self.trans_wait_list = empty_list
            self.swap_primary_secondary_deltas(trans_to_handle)
            self.change_availible.release()
            # lock released
            
            # deal with everything in trans_to_handle, reverse to reflect
            # actual order of entry
            trans_to_handle.reverse()
            while len(trans_to_handle) > 0:
                trans_delta = trans_to_handle.pop()
                # okay, this if, elif, elif looks shity, why not take
                # advantage of polymorphism here?
                if isinstance(trans_delta, TransactionDeltaManager):
                    trans = self.get_trans_for_delta(trans_delta, dbroot)
                
                    for attr, value in \
                            trans_delta.attribute_delta.iteritems():
                        setattr(trans, attr, value)
                    trans_delta.attribute_delta.clear()
                    
                    trans_delta.function_calls.reverse()
                    while len(trans_delta.function_calls) > 0:
                        (function_to_call, args, kargs) = \
                                           trans_delta.function_calls.pop()
                        function_to_call(trans, *args, **kargs)
                elif isinstance(trans_delta, TransactionDeltaEnd):
                    self.remove_delta(trans_delta)
                elif isinstance(trans_delta, TransactionThreadEnd):
                    run_thread = False

            # trans_to_handle now empty
            empty_list = trans_to_handle

            # commit the changes made
            transaction.get().commit()

        dbcon.close()
