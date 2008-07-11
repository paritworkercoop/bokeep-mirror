from persistent import Persistent

from bokeep.util import \
    ChangeMessageRecievingThread, EntityChangeManager, entitymod

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

    def set_transaction_dirty_count(self, entity_identifier, count):
        assert( count >= 0 )
        self.dirty_transaction_set[entity_identifier] = count

    def mark_transaction_dirty(self, entity_identifier):
        if entity_identifier in self.dirty_transaction_set:
            self.dirty_transaction_set[entity_identifier] += 1
        else:
            self.dirty_transaction_set[entity_identifier] = 1

    def decrement_transaction_dirty_count(self, entity_identifier, count=None):
        assert( entity_identifier in self.dirty_transaction_set )
        assert( self.dirty_transaction_set[entity_identifier] > 0 )
        assert( count > 0 )
        if count == None:
            self.dirty_transaction_set[entity_identifier] = 0
        else:
            self.dirty_transaction_set[entity_identifier] -= count

    def level_out_transaction_dirty_counts(self):
        for key, value in self.dirty_transaction_set.iteritems():
            if value > 1:
                dirty_transaction_set[key] = 1
        
    def set_backend_transaction_identifier(
        self, entity_identifier, backend_identifier):
        self.front_end_to_back_id[entity_identifier] = backend_identifier

    def get_backend_transaction_identifier(self, entity_identifier):
        if entity_identifier in self.front_end_to_back_id:
            self.front_end_to_back_id[entity_identifier] = backend_identifier
        else:
            return None

    
