from unittest import TestCase, main
from os.path import abspath
from os import remove
from glob import glob
from tempfile import NamedTemporaryFile

from bokeep.backend_modules.gnucash_backend24 import GnuCash24

from gnucash import Session, Account
from gnucash.gnucash_core_c import ACCT_TYPE_ASSET

SQLITE3 = 'sqlite3'
XML = 'xml'

ASSETS_ACCOUNT = 'Assets'
BANK_ACCOUNT = 'Bank'
PETTY_CASH_ACCOUNT = 'Petty Cash'

class GnuCash24BasicSetup(TestCase):
    def setUp(self):
        tmp = NamedTemporaryFile(
            suffix='.gnucash',
            prefix='Gnucash24_test_' + self.get_protocol(),
            dir='.')
        self.gnucash_file_name = tmp.name
        tmp.close()
        s = Session(self.get_gnucash_file_name_with_protocol(), True)
        # this is neccesary for the sqlite3 backend to work, a new
        # book has to be saved right away.
        # hope the gnucash backend module itself would need to do any
        # early saves; think this only applies to new book, wonder if
        # backend module itself should ever create a new book?
        s.save()
        book = s.get_book()
        root_account = book.get_root_account()
        CAD = book.get_table().lookup('CURRENCY', 'CAD')

        def create_new_account(name, parent=root_account):
            return_value = Account(book)
            parent.append_child(return_value)
            return_value.SetName(name)
            return_value.SetType(ACCT_TYPE_ASSET)
            return_value.SetCommodity(CAD)
            return return_value
        
        assets = create_new_account(ASSETS_ACCOUNT)
        bank = create_new_account(BANK_ACCOUNT, assets)
        petty_cash = create_new_account(PETTY_CASH_ACCOUNT, assets)
        s.save()
        s.end()

        self.backend_module = GnuCash24()
        self.backend_module.setattr(
            'gnucash_file', self.get_gnucash_file_name_with_protocol() )
        self.assert_(self.backend_module.can_write())

    def tearDown(self):
        for file_name in glob(self.gnucash_file_name + '*'):
            remove(file_name)

    def get_gnucash_file_name_with_protocol(self):
        return self.get_protocol_full() + self.gnucash_file_name

    def get_protocol(self):
        return SQLITE3

    def get_protocol_full(self):
        return self.get_protocol() + "://"

    def check_account_tree_is_present(self):
        self.backend_module.close()
        s = Session(self.get_gnucash_file_name_with_protocol())
        root = s.book.get_root_account()

        def test_for_sub_account(parent, sub_name):
            sub = parent.lookup_by_name(sub_name)
            self.assertNotEquals(sub.get_instance(), None)
            self.assertEquals(sub.GetName(), sub_name)
            return sub

        assets = test_for_sub_account(root, ASSETS_ACCOUNT)
        test_for_sub_account(assets, BANK_ACCOUNT)
        test_for_sub_account(assets, PETTY_CASH_ACCOUNT)
        
        s.end()

class GetProtocolXML(object):
    def get_protocol(self):
        return XML

class GnuCash24BasicTest(GnuCash24BasicSetup):
    test_account_tree_is_present = \
        GnuCash24BasicSetup.check_account_tree_is_present

class GnuCash24BasicTestXML(GetProtocolXML, GnuCash24BasicTest): pass

if __name__ == "__main__":
    main()
        
