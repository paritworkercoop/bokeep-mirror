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

class BasicTestSetup(TestCase):
    def setUp(self):
        self.obr = ObjectRegistry()

class BasicTest(BasicTestSetup):
    def test_same_key_add(self):
        o1 = object()
        o2 = object()
        owner = object()

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

        self.assert_(
            self.obr.final_deregister_interest_for_obj_non_unique_key(
                1, o1, owner ) )
        self.assert_(
            self.obr.final_deregister_interest_for_obj_non_unique_key(
                1, o2, owner ) )

if __name__ == "__main__":
    main()
