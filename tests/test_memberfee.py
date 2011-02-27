# Copyright (C) 2011 SkullSpace Winnipeg Inc. <andrew@andreworr.ca>
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
# Author: Andrew Orr <andrew@andreworr.ca>

import unittest
import os
import glob
import filecmp

#from bokeep.config import get_database_cfg_file
from bokeep.book import BoKeepBookSet
#from bokeep.plugins.memberfee.plugin \
#    import p


from test_bokeep_book import BoKeepWithBookSetup, TESTBOOK

MEMBERFEE_PLUGIN = 'bokeep.plugins.memberfee'

class MemberFeeTestCaseSetup(BoKeepWithBookSetup):
    def setUp(self):
        BoKeepWithBookSetup.setUp(self)
        self.books.get_book(TESTBOOK).add_module(MEMBERFEE_PLUGIN)
        self.books.get_book(TESTBOOK).enable_module(MEMBERFEE_PLUGIN)
        self.memberfee_plugin = self.books.get_book(TESTBOOK).get_module(
            MEMBERFEE_PLUGIN)

class memberTestCase(MemberFeeTestCaseSetup):
    def testMemberAddAndGet(self):
        self.assert_( self.books.has_book(TESTBOOK) )
        
if __name__ == "__main__":
    unittest.main()

