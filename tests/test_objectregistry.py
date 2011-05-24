# Copyright (C) 2011  ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
#
# This file is part of Bo-Keep.
#
# Bo-Keep is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Mark Jenkins <mark@parit.ca>

# python imports
from unittest import TestCase, main

# bokeep imports
from bokeep.objectregistry import ObjectRegistry

# zodb imports
from persistent.list import PersistentList

class TestObj(object): pass

class BasicTestSetup(TestCase):
    def setUp(self):
        self.obr = ObjectRegistry()

class BasicTest(BasicTestSetup):
    def test_same_key_add(self):
        o1 = TestObj()
        o2 = TestObj()
        owner = TestObj()

        self.obr.register_interest_by_non_unique_key(
            1, o1, owner)
        self.obr.register_interest_by_non_unique_key(
            1, o2, owner)
        result = tuple(
            val
            for val, owner in
            self.obr.registered_obj_and_owner_per_unique_key(1)
            )
        self.assert_( o1 in result and o2 in result )
        result = tuple(
            val for key, (val, owner) in
            self.obr.registered_obj_and_owner_per_unique_key_range(1,1) )
        self.assert_( o1 in result and o2 in result )

        self.assert_(hasattr(o1, '_obr_unique_key') )
        self.assert_(hasattr(o2, '_obr_unique_key') )
        self.assert_(hasattr(owner, '_obr_unique_key') )

        self.assert_(
            self.obr.final_deregister_interest_for_obj_non_unique_key(
                1, o1, owner ) )
        #self.obr.deregister_interest_by_non_unique_key(1, o1, owner)

        result = tuple(
            self.obr.registered_obj_and_owner_per_unique_key(1) )
        self.assertEquals( len(result), 1 )
        self.assert_( (o2, owner) in result )

        self.assert_(not hasattr(o1, '_obr_unique_key') )
        self.assert_(hasattr(o2, '_obr_unique_key') )
        self.assert_(hasattr(owner, '_obr_unique_key') )
        self.assert_(
            self.obr.final_deregister_interest_for_obj_non_unique_key(
                1, o2, owner ) )

    def test_diff_list_add(self):
        a = PersistentList( [ None ] )
        b = PersistentList( (None,) )
        o1 = TestObj()
        o2 = TestObj()
        self.obr.register_interest_by_non_unique_key(
            1, a, o1)
        self.obr.register_interest_by_non_unique_key(
            1, b, o1)
        self.assertEquals(len(tuple(self.obr.get_keys_for_object(a))), 1 )
        self.assertEquals(len(tuple(self.obr.get_keys_for_object(b))), 1 )
        self.assert_(
            self.obr.final_deregister_interest_for_obj_non_unique_key(
                1, a, o1 ) )
        self.assertEquals(len(tuple(self.obr.get_keys_for_object(a))), 0 )
        self.assertEquals(len(tuple(self.obr.get_keys_for_object(b))), 1 )
        
        
if __name__ == "__main__":
    main()
