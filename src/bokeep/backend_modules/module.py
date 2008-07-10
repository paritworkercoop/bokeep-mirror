from persistent import Persistent

from bokeep.util import \
    ChangeMessageRecievingThread, EntityChangeManager, entitymod

class BackendChangeManager(EntityChangeManager):
    def __init__(self, running_thread, entity_identifier):
        EntityChangeManager.__init__(self, running_thread, entity_identifier)
        self.transaction_dirty_count = 0

class BackendChangeThread(ChangeMessageRecievingThread):
    
    @entitymod
    def transaction_dirty(self, entity_identifier):
        pass

    def get_entity_from_identifier(self, entity_identifier):
        pass

    def handle_entity_change(self, entity):
        pass

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
        
    def set_backend_transaction_identifier(
        self, entity_identifier, backend_identifier):
        self.front_end_to_back_id[entity_identifier] = backend_identifier

    def get_backend_transaction_identifier(self, entity_identifier):
        if entity_identifier in self.front_end_to_back_id:
            self.front_end_to_back_id[entity_identifier] = backend_identifier
        else:
            return None

    
