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

class TestSubList(TestCase):
    def setUp(self):
        self.main_list = [1, 34, 67, 734, 'dsfs']
        self.sublist = SubList(self.main_list)
        self.sublist.paranoia = True
        self.sublist.append( 21 )
        self.sublist.append( 's6gs' )

    def test_state_after_setup(self):
        self.assertEquals( self.main_list,
                           [1, 34, 67, 734, 'dsfs', 21, 's6gs'] )

    def test_delete_zero(self):
        del self.sublist[0]
        self.assertEquals( self.main_list,
                           [1, 34, 67, 734, 'dsfs', 's6gs'] )

if __name__ == "__main__":
    main()
