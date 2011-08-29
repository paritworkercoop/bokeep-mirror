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

from unittest import TestCase, main

from bokeep.util import SubList

def make_test_for_positional_delete( main_list_match, sub_list_match,
                                     *indicies):
    def test_positional_delete(self):
        for index in indicies:
            del self.sublist[index]
        self.assertEquals( self.main_list, main_list_match )
        self.assertEquals( list(self.sublist), sub_list_match )
    return test_positional_delete

class TestSubList(TestCase):
    def setUp(self):
        self.main_list = [1, 34, 67, 734, 'dsfs']
        self.sublist = SubList(self.main_list)
        self.sublist.paranoia = True
        self.sublist.append( 21 )
        self.sublist.append( 's6gs' )
        self.sublist.append( 'abc' )

    def test_state_after_setup(self):
        self.assertEquals( self.main_list,
                           [1, 34, 67, 734, 'dsfs', 21, 's6gs', 'abc'] )
        self.assertEquals( list(self.sublist), [21, 's6gs', 'abc'] )

    test_for_zero_delete = make_test_for_positional_delete(
        [1, 34, 67, 734, 'dsfs', 's6gs', 'abc'], ['s6gs', 'abc'], 0 )

    test_for_one_delete = make_test_for_positional_delete(
        [1, 34, 67, 734, 'dsfs', 21, 'abc'], [21, 'abc'], 1 )

    test_for_two_delete = make_test_for_positional_delete(
        [1, 34, 67, 734, 'dsfs', 21, 's6gs'], [21, 's6gs'], 2 )

    test_after_double_delete_ohoh = make_test_for_positional_delete(
        [1, 34, 67, 734, 'dsfs', 'abc'], 
        ['abc'], 0, 0 )

    test_after_double_delete_ohone = make_test_for_positional_delete(
        [1, 34, 67, 734, 'dsfs', 's6gs'],
        ['s6gs'], 0, 1 )

    test_after_double_delete_two_oh = make_test_for_positional_delete(
        [1, 34, 67, 734, 'dsfs', 's6gs'],
        ['s6gs'], 2, 0 )

    test_after_double_delete_two_one = make_test_for_positional_delete(
        [1, 34, 67, 734, 'dsfs', 21],
        [21], 2, 1 )

if __name__ == "__main__":
    main()
