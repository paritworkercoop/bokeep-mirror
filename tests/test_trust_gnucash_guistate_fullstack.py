# Copyright (C) 2010  ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
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

# python
from unittest import TestCase, main
from decimal import Decimal
from os import system

# bo-keep
from bokeep.gui.state import \
    BoKeepGuiState, \
    NEW, DELETE, FORWARD, BACKWARD, TYPE_CHANGE, BOOK_CHANGE, CLOSE

# bo-keep tests
from test_bokeep_book import BoKeepWithBookSetup
from test_gnucash_backend import \
    GnuCashBasicSetup, BANK_FULL_SPEC, PETTY_CASH_FULL_SPEC

# gnucash
from gnucash import GncNumeric, Split

TRUST_PLUGIN = 'bokeep.plugins.trust'
TEST_TRUSTOR = 'testtrustor'

BACKEND_PLUGIN = 'bokeep.backend_plugins.gnucash_backend'

class BoKeepFullStackTest(BoKeepWithBookSetup, GnuCashBasicSetup):
    def setUp(self):
        BoKeepWithBookSetup.setUp(self)
        
        # set up GnuCash backend plugin
        GnuCashBasicSetup.setUp(self)
        self.backend_module.close()
        self.test_book_1.set_backend_module(BACKEND_PLUGIN)
        self.backend_module = self.test_book_1.get_backend_module()
        self.backend_module.setattr(
            'gnucash_file', self.get_gnucash_file_name_with_protocol() )

        # set up the trust plugin
        self.test_book_1.add_module(TRUST_PLUGIN)
        self.test_book_1.enable_module(TRUST_PLUGIN)
        self.trust_plugin = self.test_book_1.get_module(TRUST_PLUGIN)
        self.trust_plugin.add_trustor_by_name(TEST_TRUSTOR)
        self.trust_plugin.set_cash_account(PETTY_CASH_FULL_SPEC)
        self.trust_plugin.set_trust_liability_account(BANK_FULL_SPEC)

        # set up the gui state
        self.state = BoKeepGuiState()
        self.state.do_action(BOOK_CHANGE, self.test_book_1)

    def test_basic_transaction_with_backend_close(self):
        ONE_INT = 1
        ONE = GncNumeric(ONE_INT, 1)
        NEG_ONE = GncNumeric(-ONE_INT, 1)

        self.state.do_action(NEW)
        self.assert_(self.test_book_1.has_transaction(0))
        trust_trans = self.test_book_1.get_transaction(0)
        trust_trans.set_trustor(TEST_TRUSTOR)
        trust_trans.transfer_amount = Decimal(ONE_INT)
        self.state.do_action(CLOSE)
        self.backend_module.close()
        self.assertFalse(self.backend_module.transaction_is_clean(0))

        self.backend_module.flush_backend()
        self.assert_(self.backend_module.transaction_is_clean(0))
        self.backend_module.close()

        (s, book, root, accounts) = \
            self.acquire_gnucash_session_book_root_and_accounts()
        assets, bank, petty_cash = accounts[:3]
        bank_splits = bank.GetSplitList()
        petty_cash_splits = petty_cash.GetSplitList()
        self.assert_(petty_cash_splits[0].GetAmount().equal( ONE ) )
        self.assert_(bank_splits[0].GetAmount().equal( NEG_ONE ) )
        self.gnucash_session_termination(s)
        
    def test_basic_transaction_without_backend_close(self):
        ONE_INT = 1
        ONE = GncNumeric(ONE_INT, 1)
        NEG_ONE = GncNumeric(-ONE_INT, 1)

        self.state.do_action(NEW)
        self.assert_(self.test_book_1.has_transaction(0))
        trust_trans = self.test_book_1.get_transaction(0)
        trust_trans.set_trustor(TEST_TRUSTOR)
        trust_trans.transfer_amount = Decimal(ONE_INT)
        self.state.do_action(CLOSE)
        self.assertFalse(self.backend_module.transaction_is_clean(0))

        self.backend_module.flush_backend()
        self.assert_(self.backend_module.transaction_is_clean(0))
        self.backend_module.close()

        (s, book, root, accounts) = \
            self.acquire_gnucash_session_book_root_and_accounts()
        assets, bank, petty_cash = accounts[:3]
        bank_splits = bank.GetSplitList()
        petty_cash_splits = petty_cash.GetSplitList()
        self.assert_(petty_cash_splits[0].GetAmount().equal( ONE ) )
        self.assert_(bank_splits[0].GetAmount().equal( NEG_ONE ) )
        self.gnucash_session_termination(s)

    def test_change_transaction(self):
        self.state.do_action(NEW)
        self.state.do_action(TYPE_CHANGE, 1)

    def tearDown(self):
        self.state.do_action(CLOSE)
        GnuCashBasicSetup.tearDown(self)
        BoKeepWithBookSetup.tearDown(self)

if __name__ == "__main__":
    main()
