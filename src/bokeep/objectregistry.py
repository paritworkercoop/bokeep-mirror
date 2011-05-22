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

    def final_deregister_interest_for_obj_non_unique_key(self, key, obj, owner):
        # this is a rediculous linear implementation, the structure clearly
        # needs to be altered to nested sets instead
        da_set = self.__non_unique_key_registry.get(key)
        # filter by entries with the same object
        da_list  = [ (search_obj, search_owner)
                     for search_obj, search_owner in da_set
                     if search_obj == obj ]
        assert( len(da_list) >= 1 )
        if len(da_list) > 1:
            return False
        else:
            assert(len(da_list) == 1 )
            assert( da_list[0] == (obj, owner) )
            self.deregister_interest_by_non_unique_key(
                key, obj, owner)
            return True
