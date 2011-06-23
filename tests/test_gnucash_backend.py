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
from os.path import abspath
from os import remove
from glob import glob
from decimal import Decimal

# bokeep imports
#
# commented out because test_gnucash_backend22 imports this file
# and we don't want to cause the python bindings to be imported early
# on because the 2.2 python bindings break when that happens
#from bokeep.backend_plugins.gnucash_backend import \
#    GnuCash, call_catch_qofbackend_exception_reraise_important

from bokeep.book_transaction import \
    Transaction, FinancialTransaction, FinancialTransactionLine

# bokeep tests
from test_bokeep_book import create_tmp_filename

# commented out because test_gnucash_backend22 imports this file
# and we don't want to cause the python bindings to be imported early
# on because the 2.2 python bindings break when that happens
#
#from gnucash import Session, Account, GnuCashBackendException, Split, \
#    GncNumeric
#from gnucash.gnucash_core_c import ACCT_TYPE_ASSET, ERR_FILEIO_BACKUP_ERROR 

SQLITE3 = 'sqlite3'
XML = 'xml'
SQLITE3 = XML

ASSETS_ACCOUNT = 'Assets'
BANK_ACCOUNT = 'Bank'
PETTY_CASH_ACCOUNT = 'Petty Cash'
INCOME_ACCOUNT = 'Income'
LIABILITIES_ACCOUNT = 'Liabilities'
UNEARNED_REVENUE_ACCOUNT = 'Unearned Revenue'

ASSETS_FULL_SPEC = (ASSETS_ACCOUNT,)
BANK_FULL_SPEC = (ASSETS_ACCOUNT, BANK_ACCOUNT)
PETTY_CASH_FULL_SPEC = (ASSETS_ACCOUNT, PETTY_CASH_ACCOUNT)
INCOME_FULL_SPEC = (INCOME_ACCOUNT,)
LIABILITIES_FULL_SPEC = (LIABILITIES_ACCOUNT,)
UNEARNED_REVENUE_FULL_SPEC = (LIABILITIES_ACCOUNT, UNEARNED_REVENUE_ACCOUNT)

class TestTransaction(Transaction):
    def __init__(self, value1, account1, value2, account2):
        line1 = FinancialTransactionLine(value1)
        line1.account_spec = account1
        line2 = FinancialTransactionLine(value2)
        line2.account_spec = account2
        self.fin_trans = FinancialTransaction( (line1, line2) )
    
    def set_currency(self, currency):
        self.fin_trans.currency = currency

    def get_financial_transactions(self):
       return [self.fin_trans]

class GnuCashFileSetup(TestCase):
    def setUp(self):
        from gnucash import Account, GnuCashBackendException
        from gnucash.gnucash_core_c import \
            ACCT_TYPE_ASSET, ERR_FILEIO_BACKUP_ERROR 
        
        self.gnucash_file_name = create_tmp_filename(
            'Gnucash_test_' + self.get_protocol(),
            '.gnucash' )

        s, book, root = self.acquire_gnucash_session_book_and_root(True)
        # this is neccesary for the sqlite3 backend to work, a new
        # book has to be saved right away.
        # hope the gnucash backend module itself would need to do any
        # early saves; think this only applies to new book, wonder if
        # backend module itself should ever create a new book?
        s.save()
        currency = book.get_table().lookup('CURRENCY', self.get_currency())

        def create_new_account(name, parent):
            return_value = Account(book)
            parent.append_child(return_value)
            return_value.SetName(name)
            return_value.SetType(ACCT_TYPE_ASSET)
            return_value.SetCommodity(currency)
            return return_value
        
        assets = create_new_account(ASSETS_ACCOUNT, root)
        liabilities = create_new_account(LIABILITIES_ACCOUNT, root)
        income = create_new_account(INCOME_ACCOUNT, root)
        unearned_revenue = create_new_account(UNEARNED_REVENUE_ACCOUNT,
                                              liabilities)
        bank = create_new_account(BANK_ACCOUNT, assets)
        petty_cash = create_new_account(PETTY_CASH_ACCOUNT, assets)
        try:
            s.save()
        except GnuCashBackendException, e:
            # unless this is a file backup error, which happens when the
            # time between saves is small and is harmless, re-reise the
            # GnuCashBackendException
            if not ( len(e.errors) == 1 and \
                         e.errors[0] == ERR_FILEIO_BACKUP_ERROR ):
                raise e
        self.gnucash_session_termination(s)

    def tearDown(self):
        self.backend_module.close()
        self.assertFalse(self.backend_module.can_write())
        for file_name in glob(self.gnucash_file_name + '*'):
            remove(file_name)

    def get_currency(self):
        return "CAD"

    def get_wrong_currency(self):
        return "USD"

    def get_gnucash_file_name_with_protocol(self):
        return self.get_protocol_full() + self.gnucash_file_name

    def get_protocol(self):
        return SQLITE3

    def get_protocol_full(self):
        return self.get_protocol() + "://"

    def check_account_tree_is_present(self, session_provided=None):
        if session_provided == None:
            self.backend_module.close()
            s, book, root = self.acquire_gnucash_session_book_and_root()
        else:
            s = session_provided
            book = s.book
            root = book.get_root_account()

        def test_for_sub_account(parent, sub_name):
            sub = parent.lookup_by_name(sub_name)
            self.assertNotEquals(sub.get_instance(), None)
            self.assertEquals(sub.GetName(), sub_name)
            return sub

        self.acquire_test_accounts_from_root(root)
        
        if session_provided == None:
            self.gnucash_session_termination(s)

    def acquire_gnucash_session_book_and_root(self, is_new=False):
        from gnucash import Session
        s = Session(self.get_gnucash_file_name_with_protocol(), is_new=is_new)
        book = s.book
        root = s.book.get_root_account()
        return (s, book, root)

    def acquire_test_accounts_from_root(self, root):
        def test_for_sub_account(parent, sub_name):
            sub = parent.lookup_by_name(sub_name)
            self.assertNotEquals(sub.get_instance(), None)
            self.assertEquals(sub.GetName(), sub_name)
            return sub
        assets = test_for_sub_account(root, ASSETS_ACCOUNT)
        bank = test_for_sub_account(assets, BANK_ACCOUNT)
        petty_cash = test_for_sub_account(assets, PETTY_CASH_ACCOUNT)
        return (assets, bank, petty_cash)

    def acquire_gnucash_session_book_root_and_accounts(self):
        (s, book, root) = self.acquire_gnucash_session_book_and_root()
        return (s, book, root, self.acquire_test_accounts_from_root(root) )

    def gnucash_session_termination(self, s, with_save=False):
        from bokeep.backend_plugins.gnucash_backend import \
            call_catch_qofbackend_exception_reraise_important
        if with_save:
            call_catch_qofbackend_exception_reraise_important(s.save)
        s.end()
        s.destroy()

class GnuCashBasicSetup(GnuCashFileSetup):
    def setUp(self):
        from bokeep.backend_plugins.gnucash_backend import \
            GnuCash

        GnuCashFileSetup.setUp(self)
        self.backend_module = GnuCash()
        self.assertFalse(self.backend_module.can_write())
        self.backend_module.setattr(
            'gnucash_file', self.get_gnucash_file_name_with_protocol() )
        self.assert_(self.backend_module.can_write())       

    def tearDown(self):
        self.backend_module.close()
        self.assertFalse(self.backend_module.can_write())
        GnuCashFileSetup.tearDown(self)

class GetProtocolXML(object):
    def get_protocol(self):
        return XML

class GetCurrencyUSD(object):
    def get_currency(self):
        return "USD"

    def get_wrong_currency(self):
        return "CAD"

class GnuCashBasicTest(GnuCashBasicSetup):
    test_account_tree_is_present = \
        GnuCashBasicSetup.check_account_tree_is_present

    def do_close_and_tree_check(self):
        self.backend_module.close()
        self.assertFalse(self.backend_module.can_write() )
        self.check_account_tree_is_present()

    test_simple_close = do_close_and_tree_check

    def test_blank_flush_and_close(self):
        self.backend_module.flush_backend()
        self.assert_(self.backend_module.can_write() )
        self.do_close_and_tree_check()

    def test_imbalance(self):
        test_trans = TestTransaction(
            Decimal(1), BANK_FULL_SPEC,
            Decimal(-2), PETTY_CASH_FULL_SPEC )
        test_trans.set_currency(self.get_currency())
        front_end_id = 1
        self.backend_module.mark_transaction_dirty(
            front_end_id, test_trans)        
        self.backend_module.flush_backend()
        self.assertFalse(self.backend_module.transaction_is_clean(
                front_end_id) )
        self.assert_(
            self.backend_module.reason_transaction_is_dirty(
                front_end_id).endswith(
                "transaction doesn't balance"))

    def test_double_close(self):
        self.backend_module.close()
        self.backend_module.close()

class GnuCashBasicTestXML(GetProtocolXML, GnuCashBasicTest): pass

class GnuCashBasicTestUSD(GetCurrencyUSD, GnuCashBasicTest): pass

class GnuCashStartsWithMarkSetup(GnuCashBasicSetup):
    def setUp(self):
        GnuCashBasicSetup.setUp(self)
        self.test_trans = TestTransaction(Decimal(1), BANK_FULL_SPEC,
                                          Decimal(-1), PETTY_CASH_FULL_SPEC )
        self.test_trans.set_currency(self.get_currency())
        self.front_end_id = 1
        self.backend_module.mark_transaction_dirty(
            self.front_end_id, self.test_trans)

    def check_of_test_trans_present(self):
        from gnucash import Split, GncNumeric
        self.backend_module.close()
        
        (s, book, root, accounts) = \
            self.acquire_gnucash_session_book_root_and_accounts()
        assets, bank, petty_cash = accounts[:3]

        return_value = False
        bank_splits = bank.GetSplitList()
        petty_cash_splits = petty_cash.GetSplitList()
        ONE = GncNumeric(1, 1)
        NEG_ONE = GncNumeric(-1, 1)

        # perhaps we this restriction be done away with to make the
        # test more flexible and the actual transaction of interest
        # fished out amougst others (if they exist)
        #
        # but there is an upside to this retriction, when the transaction
        # is being delete and re-created a lot, checking for one and only
        # transaction helps ensure that the going away side really is happening
        if len(bank_splits) == 1 and len(petty_cash_splits) == 1:
            if bank_splits[0].GetAmount().equal( ONE ):
                if petty_cash_splits[0].GetAmount().equal(NEG_ONE):
                    return_value = True
        
        self.gnucash_session_termination(s)

        return return_value

class GnuCashStartsWithMarkTests(GnuCashStartsWithMarkSetup):   
    def test_simple_flush(self):
        self.backend_module.flush_backend()
        if not self.backend_module.transaction_is_clean(
                self.front_end_id):
            self.assertEquals(
                self.backend_module.reason_transaction_is_dirty(
                    self.front_end_id),
                None)
        self.assert_(self.backend_module.transaction_is_clean(
                self.front_end_id ))
        self.assert_(self.check_of_test_trans_present())
        self.check_account_tree_is_present()

    def test_close_flush_close(self):
        self.assertFalse(self.check_of_test_trans_present())
        self.backend_module.flush_backend()
        self.assert_(self.check_of_test_trans_present())
        self.check_account_tree_is_present()

    def test_close_account_commod_change_then_flush(self):
        self.backend_module.close()

        self.assertFalse(self.backend_module.transaction_is_clean(
                self.front_end_id) )
        # why not clean, the reason should be checked?

        (s, book, root, accounts) = \
            self.acquire_gnucash_session_book_root_and_accounts()
        assets, bank, petty_cash = accounts[:3] 
        commod_table = book.get_table()
        wrong = commod_table.lookup("ISO4217", self.get_wrong_currency() )
        bank.SetCommodity(wrong)
        self.gnucash_session_termination(s, True)

        # perhaps doing a flush first,
        # this damage second, and verify here should also be able to
        # trigger the transaction being marked dirty
        self.backend_module.flush_backend()
        self.assertFalse(self.backend_module.transaction_is_clean(
                self.front_end_id) )
        reason_dirty = \
            self.backend_module.reason_transaction_is_dirty(self.front_end_id)
        self.assert_(reason_dirty.endswith(
                "transaction currency and account don't match") )       

    def test_bad_account_path(self):
        self.test_trans.fin_trans.lines[0].account_spec = ("garbage",)
        self.backend_module.flush_backend()
        self.assertFalse(self.backend_module.transaction_is_clean(
                self.front_end_id) )
        self.assert_(
            self.backend_module.reason_transaction_is_dirty(
                self.front_end_id).endswith(
                "path garbage could not be found"))
        self.test_trans.fin_trans.lines[0].account_spec = BANK_FULL_SPEC
        self.backend_module.flush_backend()
        self.assert_(self.backend_module.transaction_is_clean(
                self.front_end_id))
        self.assert_(self.check_of_test_trans_present())
        # should do a flush, screw it up, re-flush and check for
        # transaction removal but not recreation as well


    def check_if_transaction_is_missing(self):
        from gnucash import Split
        self.backend_module.close()
        (s, book, root, accounts) = \
            self.acquire_gnucash_session_book_root_and_accounts()
        assets, bank, petty_cash = accounts[:3]

        return_value = False
        bank_splits = bank.GetSplitList()
        petty_cash_splits = petty_cash.GetSplitList()
        self.assertEquals(len(bank_splits), 0)
        self.assertEquals(len(petty_cash_splits), 0)
        self.gnucash_session_termination(s)

    def test_bad_account_removes_success_trans(self):
        self.backend_module.flush_backend()
        self.assert_(self.check_of_test_trans_present())
        self.assert_(self.backend_module.transaction_is_clean(
                self.front_end_id) )
        self.test_trans.fin_trans.lines[0].account_spec = ("garbage",)
        self.backend_module.mark_transaction_dirty(
            self.front_end_id, self.test_trans)
        self.backend_module.flush_backend()
        self.assertFalse(self.backend_module.transaction_is_clean(
                self.front_end_id) )
        self.assert_(
            self.backend_module.reason_transaction_is_dirty(
                self.front_end_id).endswith(
                "path garbage could not be found"))
        self.check_if_transaction_is_missing()

        # should do a flush, screw it up, re-flush and check for
        # transaction removal but not recreation as well
        self.test_trans.fin_trans.lines[0].account_spec = BANK_FULL_SPEC
        self.assertFalse(
            self.backend_module.transaction_is_clean(self.front_end_id))
        self.backend_module.flush_backend()
        self.assert_(
            self.backend_module.transaction_is_clean(self.front_end_id))
        self.assert_(self.check_of_test_trans_present())

class GnuCashStartsWithMarkTestsXML(
    GetProtocolXML, GnuCashStartsWithMarkTests):
    pass

class GnuCashStartsWithMarkTestsUSD(
    GetCurrencyUSD, GnuCashStartsWithMarkTests):
    pass

if __name__ == "__main__":
    main()

