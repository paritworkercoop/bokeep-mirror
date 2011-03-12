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
from bokeep.plugins.memberfee.plugin \
    import FeeCollection

from test_bokeep_book import BoKeepWithBookSetup, TESTBOOK
from decimal import Decimal
from datetime import date

MEMBERFEE_PLUGIN = 'bokeep.plugins.memberfee'

class MemberFeeTestCaseSetup(BoKeepWithBookSetup):
    def setUp(self):
        BoKeepWithBookSetup.setUp(self)
        self.test_book_1 = self.books.get_book(TESTBOOK)
        self.test_book_1.add_module(MEMBERFEE_PLUGIN)
        self.test_book_1.enable_module(MEMBERFEE_PLUGIN)
        self.memberfee_plugin = self.test_book_1.get_module(
            MEMBERFEE_PLUGIN)
        self.feetrans = FeeCollection(self.memberfee_plugin)
        self.feetrans.collection_date = date(2011, 1, 1)
        self.bokeep_trans_id = self.test_book_1.insert_transaction(
            self.feetrans)
        self.memberfee_plugin.register_transaction(
            self.bokeep_trans_id, self.feetrans)

class memberTestCase(MemberFeeTestCaseSetup):
    def testMemberAddAndGet(self):
        self.assert_( self.books.has_book(TESTBOOK) )

    
class memberAfterSpreadSetup(MemberFeeTestCaseSetup):
    def setUp(self):
        super(memberAfterSpreadSetup, self).setUp()
        self.feetrans.collected = Decimal(40)
        self.feetrans.spread_collected(date(2011, 1, 1), 1, Decimal(10))

class memberAfterSpreadTestCase(memberAfterSpreadSetup):
    def testSpreadAmount(self):
        for i,(test_date, test_value) in enumerate(
            self.feetrans.periods_applied_to):
            self.assertEquals(date(2011,i+1,1), test_date)
            self.assertEquals(Decimal(10), test_value)

    def testPeriodsAndCollectedMatch(self):
        self.assert_(self.feetrans.periods_and_collected_match())

    def testCollectionBackendFinTrans(self):
        fin_trans_list = list(self.feetrans.get_financial_transactions())
        for i,(trans_date, value) in enumerate(
            ( (self.feetrans.collection_date, 40),
              (date(2011, 1, 1), 10 ),
              (date(2011, 2, 1), 10 ),
              (date(2011, 3, 1), 10 ), 
              (date(2011, 4, 1), 10 ) ) ):
            lines = fin_trans_list[i].lines
            self.assertEquals( trans_date, fin_trans_list[i].trans_date )
            self.assertEquals( lines[0].amount, value )
                    
if __name__ == "__main__":
    unittest.main()

