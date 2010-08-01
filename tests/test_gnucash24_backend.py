from unittest import TestCase, main
from os.path import abspath
from os import remove
from glob import glob
from tempfile import NamedTemporaryFile
from decimal import Decimal

from bokeep.backend_modules.gnucash_backend24 import GnuCash24
from bokeep.book_transaction import \
    Transaction, FinancialTransaction, FinancialTransactionLine

from gnucash import Session, Account, GnuCashBackendException, Split, \
    GncNumeric
from gnucash.gnucash_core_c import ACCT_TYPE_ASSET, ERR_FILEIO_BACKUP_ERROR 

SQLITE3 = 'sqlite3'
XML = 'xml'

ASSETS_ACCOUNT = 'Assets'
BANK_ACCOUNT = 'Bank'
PETTY_CASH_ACCOUNT = 'Petty Cash'

ASSETS_FULL_SPEC = (ASSETS_ACCOUNT)
BANK_FULL_SPEC = (ASSETS_ACCOUNT, BANK_ACCOUNT)
PETTY_CASH_FULL_SPEC = (ASSETS_ACCOUNT, PETTY_CASH_ACCOUNT)

class TestTransaction(Transaction):
    def __init__(self, value1, account1, value2, account2):
        line1 = FinancialTransactionLine(value1)
        line1.account_spec = account1
        line2 = FinancialTransactionLine(value2)
        line2.account_spec = account2
        self.fin_trans = FinancialTransaction( (line1, line2) )
    
    def get_financial_transactions(self):
       return [self.fin_trans]

class GnuCash24BasicSetup(TestCase):
    def setUp(self):
        tmp = NamedTemporaryFile(
            suffix='.gnucash',
            prefix='Gnucash24_test_' + self.get_protocol(),
            dir='.')
        self.gnucash_file_name = tmp.name
        tmp.close()
        s, book, root = self.acquire_gnucash_session_book_and_root(True)
        # this is neccesary for the sqlite3 backend to work, a new
        # book has to be saved right away.
        # hope the gnucash backend module itself would need to do any
        # early saves; think this only applies to new book, wonder if
        # backend module itself should ever create a new book?
        s.save()
        CAD = book.get_table().lookup('CURRENCY', 'CAD')

        def create_new_account(name, parent):
            return_value = Account(book)
            parent.append_child(return_value)
            return_value.SetName(name)
            return_value.SetType(ACCT_TYPE_ASSET)
            return_value.SetCommodity(CAD)
            return return_value
        
        assets = create_new_account(ASSETS_ACCOUNT, root)
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

        self.backend_module = GnuCash24()
        self.assertFalse(self.backend_module.can_write())
        self.backend_module.setattr(
            'gnucash_file', self.get_gnucash_file_name_with_protocol() )
        self.assert_(self.backend_module.can_write())

    def tearDown(self):
        self.backend_module.close()
        self.assertFalse(self.backend_module.can_write())
        for file_name in glob(self.gnucash_file_name + '*'):
            remove(file_name)

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
        s = Session(self.get_gnucash_file_name_with_protocol(), is_new)
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
        if with_save:
            s.save()
        s.end()
        s.destroy()


class GetProtocolXML(object):
    def get_protocol(self):
        return XML

class GnuCash24BasicTest(GnuCash24BasicSetup):
    test_account_tree_is_present = \
        GnuCash24BasicSetup.check_account_tree_is_present

    def do_close_and_tree_check(self):
        self.backend_module.close()
        self.assertFalse(self.backend_module.can_write() )
        self.check_account_tree_is_present()

    test_simple_close = do_close_and_tree_check

    def test_blank_flush_and_close(self):
        self.backend_module.flush_backend()
        self.assert_(self.backend_module.can_write() )
        self.do_close_and_tree_check()

class GnuCash24BasicTestXML(GetProtocolXML, GnuCash24BasicTest): pass

class GnuCash24StartsWithMarkSetup(GnuCash24BasicSetup):
    def setUp(self):
        GnuCash24BasicSetup.setUp(self)
        self.test_trans = TestTransaction(Decimal(1), BANK_FULL_SPEC,
                                          Decimal(-1), PETTY_CASH_FULL_SPEC )
        self.front_end_id = 1
        self.backend_module.mark_transaction_dirty(
            self.front_end_id, self.test_trans)

    def check_of_test_trans_present(self):
        self.backend_module.close()
        
        (s, book, root, accounts) = \
            self.acquire_gnucash_session_book_root_and_accounts()
        assets, bank, petty_cash = accounts[:3]

        return_value = False
        bank_splits = [Split(instance=split_inst)
                       for split_inst in bank.GetSplitList() ]
        petty_cash_splits = [Split(instance=split_inst)
                             for split_inst in petty_cash.GetSplitList() ]
        ONE = GncNumeric(1)
        NEG_ONE = GncNumeric(-1)
        # perhaps we this restriction be done away with to make the
        # test more flexible and the actual transaction of interest
        # fished out amougst others (if they exist)
        if len(bank_splits) == 1 and len(petty_cash_splits) == 1:
            # compare the bank account splists
            if bank_splits[0].GetAmount().equal( ONE ):
                if petty_cash_splits[0].GetAmount().equal(NEG_ONE):
                    return_value = True
        
        self.gnucash_session_termination(s)

        return return_value

class GnuCash24StartsWithMarkTests(GnuCash24StartsWithMarkSetup):   
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

        (s, book, root, accounts) = \
            self.acquire_gnucash_session_book_root_and_accounts()
        assets, bank, petty_cash = accounts[:3] 
        commod_table = book.get_table()
        USD = commod_table.lookup("ISO4217","USD")
        bank.SetCommodity(USD)
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

if __name__ == "__main__":
    main()
        
