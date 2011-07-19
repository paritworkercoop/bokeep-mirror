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
from itertools import izip

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

def do_logger_function(original_func):
    def logger_function(self, *args, **kargs):
        self.log.append(None)
        pos = len(self.log)-1
        return_value = original_func(self, *args, **kargs)
        self.log[pos] = (
            "%s called with %s and %s and returned %s" %
            (original_func.__name__, args, kargs, return_value) )
        return return_value
    return logger_function

class SerialFileLogingPlugin(SerialFilePlugin):
    def __init__(self):
        SerialFilePlugin.__init__(self)
        self.log = []

    def get_log(self):
        return self.log

for func_name in ("open_session", "write_to_file", "close", "save"):
    setattr(SerialFileLogingPlugin, func_name,
            do_logger_function( getattr(SerialFilePlugin, func_name) ) )

class SerialFileTest(TestCase):
    def setUp(self):
        self.serial_file_name = create_tmp_filename(
            'serialfile_test', '.txt' )    
        
        self.test_trans = TestTransaction(
            Decimal(2), None,
            Decimal(-2), None )
        self.front_end_id = 1
        self.backend_plugin = SerialFileLogingPlugin()
        self.backend_plugin.accounting_file = self.serial_file_name
        self.do_mark_flush_and_check()

    def do_dirty_mark(self):
        self.backend_plugin.mark_transaction_dirty(
            self.front_end_id, self.test_trans)
        
    def do_mark_flush_and_check(self):
        self.do_dirty_mark()
        self.backend_plugin.flush_backend()
        self.do_can_write_test()
        self.do_clean_and_can_write_test()

    def do_clean_and_can_write_test(self):
        self.assert_(
            self.backend_plugin.transaction_is_clean(self.front_end_id))
        self.do_can_write_test()

    def do_can_write_test(self):
        self.assert_(self.backend_plugin.can_write())

    def test_log_has_right_number_of_ops(self):
        log = self.backend_plugin.get_log()
        self.assertEquals( len(log), 4 )

        for i, (prefix, log_entry) in enumerate(izip(
        ("open_session", "write_to_file", "save", "open_session"),
        log )):
            log_entry_start = log_entry[ :len(prefix) ]
            self.assertEquals(log_entry_start, prefix)

    def test_second_mark_and_flush(self):
        self.do_dirty_mark()
        self.do_can_write_test()
        self.backend_plugin.flush_backend()
        self.do_can_write_test()
        self.do_clean_and_can_write_test()

    def test_flush_no_re_dirty_mark(self):
        self.backend_plugin.flush_backend()
        self.do_clean_and_can_write_test()

    def tearDown(self):
        self.backend_plugin.close()
        remove(self.serial_file_name)
            
if __name__ == "__main__":
    main()


