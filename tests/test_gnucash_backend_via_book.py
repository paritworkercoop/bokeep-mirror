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

# This test can only be run directly
# $ python tests/tests/test_gnucash_backend_via_book.py and not via the
# $ ./setup.py test because it actually tries to persist in
# bokeep.book.BoKeepBook a transaction type created here and not one from
# a normally found path

from unittest import main
from decimal import Decimal

from bokeep.book_transaction import \
    Transaction, FinancialTransaction, FinancialTransactionLine

from test_gnucash_backend import \
    GnuCashFileSetup, TestTransaction, BANK_FULL_SPEC, PETTY_CASH_FULL_SPEC

from test_bokeep_book import BoKeepWithBookSetup

BACKEND_PLUGIN = 'bokeep.backend_plugins.gnucash_backend'

class TestGnuCashBackendViaBook(GnuCashFileSetup, BoKeepWithBookSetup):
    def setUp(self):
        GnuCashFileSetup.setUp(self)

        BoKeepWithBookSetup.setUp(self)

        self.test_book_1.set_backend_plugin(BACKEND_PLUGIN)
        self.backend_plugin = self.test_book_1.get_backend_plugin()
        self.backend_plugin.setattr(
            'gnucash_file', self.get_gnucash_file_name_with_protocol() )

    def test_test_transaction_mark_and_flush(self):

        trans = TestTransaction( Decimal(1), BANK_FULL_SPEC,
                                 Decimal(-1), PETTY_CASH_FULL_SPEC )
        trans_id = 1
        self.backend_plugin.mark_transaction_dirty(trans_id, trans)
        
        self.backend_plugin.flush_backend()
        if not self.backend_plugin.transaction_is_clean(trans_id):
            self.assertEquals(
                self.backend_plugin.reason_transaction_is_dirty(trans_id),
                None)
        self.assert_(self.backend_plugin.transaction_is_clean(trans_id))

    def tearDown(self):
        GnuCashFileSetup.tearDown(self)
        BoKeepWithBookSetup.tearDown(self)

if __name__ == "__main__":
    main()

