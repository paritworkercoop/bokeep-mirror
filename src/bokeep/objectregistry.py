# zodb imports
from persistent import Persistent
from persistent.mapping import PersistentMapping
from BTrees.OOBTree import OOBTree as BTree, OOSet as Set
from BTrees.IOBTree import IOBTree

# bokeep imports
from bokeep.util import get_and_establish_attribute

class ObjectRegistry(Persistent):
    def __init__(self):
        self.__non_unique_key_registry = BTree()
        self.__obr_registry = IOBTree()
        self.__obr_largest_key_ever = -1
        self.__non_unique_keys_for_obj = IOBTree()

    def get_keys_for_object(self, obj):
        if (not hasattr(obj, '_obr_unique_key') or
             not self.__non_unique_keys_for_obj.has_key(obj._obr_unique_key) ):
            return ()
        else:
            return self.__non_unique_keys_for_obj[obj._obr_unique_key]

    def __register_object(self, obj):
        obr_unique_key = get_and_establish_attribute(
                obj, '_obr_unique_key',
                lambda: (0 if len(self.__obr_registry) == 0
                         else max(self.__obr_registry.maxKey() + 1,
                                  self.__obr_largest_key_ever + 1 ) )
                )
        self.__obr_registry[obr_unique_key] = obj
        self.__obr_largest_key_ever = max(obr_unique_key,
                                          self.__obr_largest_key_ever )
        self.__non_unique_keys_for_obj[obr_unique_key] = Set()
        return obr_unique_key
    
    def __deregister_object(self, obj):
        obj_key = obj._obr_unique_key
        if self.__non_unique_keys_for_obj.has_key(obj_key):
            assert( len(self.__non_unique_keys_for_obj[obj_key]) == 0 )
            del self.__non_unique_keys_for_obj[obj_key]
        del self.__obr_registry[obj_key]
        delattr(obj, '_obr_unique_key')

    def register_interest_by_non_unique_key(
        self, key, obj, owner):
        obj_key, owner_key = \
            self.__register_object(obj), self.__register_object(owner)
        set_for_key = self.__non_unique_key_registry.setdefault(key, Set())
        set_for_key.insert( (obj_key, owner_key) )
        for obr_unique_key in obj_key, owner_key:
            self.__non_unique_keys_for_obj[obr_unique_key].insert( key )

    def registered_obj_and_owner_per_unique_key(self, key):
        return ( (self.__obr_registry[obj_key], self.__obr_registry[owner_key])
                 for obj_key, owner_key
                 in self.__non_unique_key_registry.get(key,() )
                 ) # end generator expression
            

    def registered_obj_and_owner_per_unique_key_range(self, key_min, key_max):
        return ( (key, (self.__obr_registry[obj_key],
                        self.__obr_registry[owner_key]) ) # end tuple
                 for (key, da_set)
                 in self.__non_unique_key_registry.iteritems(key_min, key_max)
                 for (obj_key, owner_key) in da_set
                 ) # end generator expression
    
    def deregister_interest_by_non_unique_key(self, key, obj, owner):
        obj_key = obj._obr_unique_key
        owner_key = owner._obr_unique_key
        self.__non_unique_key_registry.get(key).remove( (obj_key, owner_key) )

        # this is sort of rediculous counting up all the references for
        # obj and owner and making a deletion decision on that
        # when we could of just kept count them all along
        obj_count = 0
        owner_count = 0
        for obj_search, owner_search in \
            self.registered_obj_and_owner_per_unique_key(key):
            obj_search_key = obj_search._obr_unique_key
            owner_search_key = owner_search._obr_unique_key
            if obj_search_key == obj_key: obj_count+=1
            if owner_search_key == owner_key: owner_count+=1
        for count, da_obj_key, da_obj in \
                ( (obj_count, obj_key, obj), (owner_count, owner_key, owner) ):
            if count == 0:
                self.__non_unique_keys_for_obj[da_obj_key].remove(key)
                self.__deregister_object(da_obj)

    def final_deregister_interest_for_obj_non_unique_key(self, key, obj, owner):
        obj_key = obj._obr_unique_key
        owner_key = owner._obr_unique_key
        # this is a rediculous linear implementation, the structure clearly
        # needs to be altered to nested sets instead
        da_set = self.__non_unique_key_registry.get(key)
        # filter by entries with the same object
        da_list  = [ (search_obj_key, search_owner_key)
                     for search_obj_key, search_owner_key in da_set
                     if search_obj_key == obj_key ]
        assert( len(da_list) >= 1 )
        if len(da_list) > 1:
            return False
        else:
            assert(len(da_list) == 1 )
            assert( da_list[0] == (obj_key, owner_key) )
            self.deregister_interest_by_non_unique_key(
                key, obj, owner)
            return True
