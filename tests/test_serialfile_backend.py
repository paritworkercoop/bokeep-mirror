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
from os.path import abspath
from os import remove
from decimal import Decimal

# bokeep
from bokeep.book_transaction import \
    Transaction, FinancialTransaction, FinancialTransactionLine
from bokeep.backend_plugins.serialfile import SerialFilePlugin

# bokeep test suite
from test_bokeep_book import create_tmp_filename

class TestTransaction(Transaction):
    def __init__(self, value1, account1, value2, account2):
        line1 = FinancialTransactionLine(value1)
        line1.account_spec = account1
        line2 = FinancialTransactionLine(value2)
        line2.account_spec = account2
        self.fin_trans = FinancialTransaction( (line1, line2) )
    
    def get_financial_transactions(self):
       return [self.fin_trans]

class SerialFileTest(TestCase):
    def setUp(self):
        self.serial_file_name = create_tmp_filename(
            'serialfile_test', '.txt' )    
        
        self.test_trans = TestTransaction(
            Decimal(2), None,
            Decimal(-2), None )
        self.front_end_id = 1
        self.backend_module = SerialFilePlugin()
        self.backend_module.accounting_file = self.serial_file_name
        self.do_mark_flush_and_check()

    def do_dirty_mark(self):
        self.backend_module.mark_transaction_dirty(
            self.front_end_id, self.test_trans)
        
    def do_mark_flush_and_check(self):
        self.do_dirty_mark()
        self.backend_module.flush_backend()
        self.do_can_write_test()
        self.do_clean_and_can_write_test()

    def do_clean_and_can_write_test(self):
        self.assert_(
            self.backend_module.transaction_is_clean(self.front_end_id))
        self.do_can_write_test()

    def do_can_write_test(self):
        self.assert_(self.backend_module.can_write())

    test_second_mark_and_flush = do_mark_flush_and_check

    def test_flush_no_re_dirty_mark(self):
        self.backend_module.flush_backend()
        self.do_clean_and_can_write_test()

    def tearDown(self):
        remove(self.serial_file_name)
            
if __name__ == "__main__":
    main()


