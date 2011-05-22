from persistent import Persistent
from persistent.mapping import PersistentMapping
from BTrees.OOBTree import BTree, Set

class ObjectRegistry(Persistent):
    def __init__(self):
        self.__non_unique_key_registry = BTree()
        self.__unique_key_registry = PersistentMapping()

    def register_interest_by_non_unique_key(
        self, key, obj, owner):
        set_for_key = self.__non_unique_key_registry.setdefault(key, Set())
        set_for_key.add( (obj, owner) )

    def registered_obj_and_owner_per_unique_key(self, key):
        return self.__non_unique_key_registry.get(key, () )

    def registered_obj_and_owner_per_unique_key_range(self, key_min, key_max):
        return ( (key, pair)
                 for (key, da_set) in self.__non_unique_key_registry.iteritems(
                key_min, key_max)
                 for pair in da_set )
            
    def deregister_interest_by_non_unique_key(self, key, obj, owner):
        self.__non_unique_key_registry.get(key).remove( (obj, owner) )
