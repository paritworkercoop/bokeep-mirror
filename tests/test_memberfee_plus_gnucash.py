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
from test_memberfee import memberAfterSpreadSetup
from test_gnucash_backend import \
    GnuCashBasicSetup, PETTY_CASH_FULL_SPEC, INCOME_FULL_SPEC, \
    UNEARNED_REVENUE_FULL_SPEC

from os import system

BACKEND_PLUGIN = 'bokeep.backend_plugins.gnucash_backend'

class MemberFeeGnucashTestCaseSetup(memberAfterSpreadSetup, GnuCashBasicSetup):
    def setUp(self):
        memberAfterSpreadSetup.setUp(self)
        GnuCashBasicSetup.setUp(self)
        self.backend_module.close()
        self.test_book_1.set_backend_module(BACKEND_PLUGIN)
        self.backend_module = self.test_book_1.get_backend_module()
        self.backend_module.setattr(
            'gnucash_file', self.get_gnucash_file_name_with_protocol() )
        self.memberfee_plugin.set_income_account(INCOME_FULL_SPEC)
        self.memberfee_plugin.set_unearned_account(
            UNEARNED_REVENUE_FULL_SPEC)
        self.memberfee_plugin.set_cash_account(PETTY_CASH_FULL_SPEC)
        self.backend_module.mark_transaction_dirty(self.bokeep_trans_id,
                                                   self.feetrans)
        self.backend_module.flush_backend()

    def test_sucess_flush(self):
        self.assertEquals(
            self.backend_module.reason_transaction_is_dirty(
                self.bokeep_trans_id),
            None)
        self.assert_(
            self.backend_module.transaction_is_clean(self.bokeep_trans_id))

# should really write some python binding code to check things worked
#    def testLeaveGnucashFile(self):
#        self.backend_module.close()
#        system('cp %s %s' %(self.gnucash_file_name,
#                            'andrew_and_mark_are_peeking.gnucash'))

if __name__ == "__main__":
    unittest.main()
