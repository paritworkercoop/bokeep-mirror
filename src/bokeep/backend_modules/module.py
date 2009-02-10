from persistent import Persistent

from bokeep.book_transaction import \
    BoKeepTransactionNotMappableToFinancialTransaction

from bokeep.util import \
    ChangeMessageRecievingThread, EntityChangeManager, entitymod, \
    ends_with_commit

class BackendChangeManager(EntityChangeManager):
    def __init__(self, running_thread, entity_identifier):
        EntityChangeManager.__init__(self, running_thread, entity_identifier)
        self.transaction_dirty_count = 0

    def increment(self):
        self.transaction_dirty_count += 1
    
    def send_to_zero(self):
        return_value = self.transaction_dirty_count
        self.transaction_dirty_count = 0
        return return_value
 

class BackendChangeThread(ChangeMessageRecievingThread):
    
    @entitymod
    def mark_transaction_dirty(self, change_manager, entity_identifier):
        change_manager.increment()

    def get_entity_from_identifier(self, entity_identifier):
        pass

    def handle_entity_change(self, change_message, entity):
        # change required, only do this if backend is co-operative, if it
        # is locked or something ,imform other that it is still dirty
        # I wonder if we can avoid this...
        count_down = change_message.send_to_zero()
        
        # put representation of entity identified by
        # change_message.entity_identifier, and old backend id
        # to backend, receie returned backenend id and store
        #
        # send count_down back to the backend module dirty db, or nothing

class BackendModule(Persistent):
    def __init__(self):
        Persistent.__init__(self)
        self.dirty_transaction_set = {}
        self.front_end_to_back_id = {}

    def mark_transaction_dirty(self, entity_identifier, transaction):
        if entity_identifier not in self.dirty_transaction_set:
            self.dirty_transaction_set[entity_identifier] = transaction
        
    def set_backend_transaction_identifier(
        self, entity_identifier, backend_identifier):
        self.front_end_to_back_id[entity_identifier] = backend_identifier

    def get_backend_transaction_identifier(self, entity_identifier):
        if entity_identifier in self.front_end_to_back_id:
            self.front_end_to_back_id[entity_identifier] = backend_identifier
        else:
            return None

    def can_write(self):
       # The superclass for all BackendModule s can never write, 
       # because it is a just a base class, you should subclass and
       # return True here when appropriate
       return False

    def remove_backend_transaction(self, backend_ident):
        raise Exception("backend modules must implement "
                        "remove_backend_transaction")

    def create_backend_transaction(self, fin_trans):
        """Create a transaction inside the actual backend based on fin_trans
        """
        raise Exception("backend modules must implement "
                        "create_backend_transaction")

    def save(self):
        raise Exception("backend modules must implement save()")

    def flush_transaction(self, entity_identifier):
        if None != self.get_backend_transaction_identifier(entity_identifier):
            self.remove_backend_transaction(entity_identifier)

        # get financial transactions from the specified bokeep transaction
        # put each of these in the backend, and store a mapping of the
        # bokeep transaction identifier and the associated backend transactions
        transaction = self.dirty_transaction_set[entity_identifier]
        self.set_backend_transaction_identifier(
            entity_identifier,
            tuple( 
                self.create_backend_transaction(fin_trans)
                for fin_trans in transaction.get_financial_transactions() )
            )
    
    @ends_with_commit
    def flush_backend(self):
        """Take all dirty transactions and write them out if possible
        """
        # if we can write to the backend
        if self.can_write():
            not_flushable_set = {}
            # for each dirty transaction
            for key, value in self.dirty_transaction_set.iteritems():
                try:
                    self.flush_transaction(key)
                except BoKeepTransactionNotMappableToFinancialTransaction:
                    not_flushable_set[key] = value
            self.save()
            self.dirty_transaction_set = not_flushable_set
