from persistent import Persistent

from bokeep.util import \
    ChangeMessageRecievingThread, EntityChangeManager, entitymod

class BackendChangeManager(EntityChangeManager):
    def __init__(self, running_thread, entity_identifier):
        EntityChangeManager.__init__(self, running_thread, entity_identifier)
        self.transaction_dirty = False

class BackendChangeThread(ChangeMessageRecievingThread):
    
    @entitymod
    def transaction_dirty(self, entity_identifier):
        pass

    def get_entity_from_identifier(self, entity_identifier):
        pass

    def handle_entity_change(self, entity):
        pass

class BackendModule(Persistent):
    def __init__(self, database):
        Persistent.__init__(self)
        self._v_change_thread = BackendChangeThread()
        self._v_change_thread.run()

    def transaction_dirty(self, entity_identifier):
        pass

