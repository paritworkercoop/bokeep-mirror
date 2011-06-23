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

# python
from unittest import TestCase, main
from decimal import Decimal
from os import system

# bo-keep
from bokeep.plugins.trust import TrustTransaction, TrustModule

# bo-keep tests
from test_bokeep_book import BoKeepWithBookSetup
from test_gnucash_backend import \
    GnuCashBasicSetup, BANK_FULL_SPEC, PETTY_CASH_FULL_SPEC

# gnucash
from gnucash import GncNumeric, Split

TRUST_PLUGIN = 'bokeep.plugins.trust'
TEST_TRUSTOR = 'testtrustor'

BACKEND_PLUGIN = 'bokeep.backend_plugins.gnucash_backend'

class SimplerTrustTest(GnuCashBasicSetup):
    def setUp(self):
        # set up GnuCash backend plugin
        GnuCashBasicSetup.setUp(self)
        self.trust_plugin = TrustModule()
        self.trust_plugin.add_trustor_by_name(TEST_TRUSTOR)
        self.trust_plugin.set_cash_account(PETTY_CASH_FULL_SPEC)
        self.trust_plugin.set_trust_liability_account(BANK_FULL_SPEC)        

    def test_me(self):
        trans = TrustTransaction(self.trust_plugin)
        trans_id = 1
        self.backend_module.mark_transaction_dirty(trans_id, trans)
        self.backend_module.flush_backend()
        if not self.backend_module.transaction_is_clean(trans_id):
            self.assertEquals(
                self.backend_module.reason_transaction_is_dirty(trans_id),
                None)
        self.assert_(self.backend_module.transaction_is_clean(trans_id))

    def tearDown(self):
        GnuCashBasicSetup.tearDown(self)

class BoKeepTrustGnuCashTestSetup(BoKeepWithBookSetup, GnuCashBasicSetup):
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

    def tearDown(self):
        GnuCashBasicSetup.tearDown(self)
        BoKeepWithBookSetup.tearDown(self)


class BoKeepTrustGnuCashTest(BoKeepTrustGnuCashTestSetup):
    def test_me(self):
        trans = TrustTransaction(self.trust_plugin)
        trans_id = self.test_book_1.insert_transaction(trans)
        self.trust_plugin.register_transaction(trans_id, trans)
        self.backend_module.mark_transaction_dirty(trans_id, trans)
        self.backend_module.flush_backend()
        self.assertEquals(
            self.backend_module.reason_transaction_is_dirty(trans_id),
            None)
        self.assert_(self.backend_module.transaction_is_clean(trans_id))

if __name__ == "__main__":
    main()
