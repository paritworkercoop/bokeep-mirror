# python
from unittest import TestCase, main
from decimal import Decimal

# bokeep
from bokeep.backend_plugins.gnucash_backend_22 import \
    GnuCash22 as GnuCash

# bokeep tests
# hopefully we don't get in trouble for importing from a module that
# does gnucash module importing, as that can lead to bad news!
from test_gnucash_backend import \
    GnuCashBasicSetup, GnuCashBasicTest, \
    GnuCashStartsWithMarkSetup, GnuCashStartsWithMarkTests, \
    TestTransaction, \
    ASSETS_ACCOUNT, BANK_ACCOUNT, PETTY_CASH_ACCOUNT, \
    ASSETS_FULL_SPEC, BANK_FULL_SPEC, PETTY_CASH_FULL_SPEC

# bokeep tests
from test_bokeep_book import create_tmp_filename

FILEPROTOCOL = 'file'

class GnuCashBasicSetup22(GnuCashBasicSetup):
    def setUp(self):
        from gnucash import Account, GncCommodityTable, \
            ERR_FILEIO_BACKUP_ERROR, GnuCashBackendException
        from gnucash.gnucash_core_c import \
            ACCT_TYPE_ASSET, \
            gnc_commodity_table_get_table, gnc_commodity_table_lookup
        
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
        commod_table = GncCommodityTable(
            instance=gnc_commodity_table_get_table(
                s.book.get_instance()) )
        CAD = gnc_commodity_table_lookup(
            commod_table.get_instance(), "ISO4217","CAD")

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

        self.backend_module = GnuCash()
        self.assertFalse(self.backend_module.can_write())
        self.backend_module.setattr(
            'gnucash_file', self.get_gnucash_file_name_with_protocol() )
        self.assert_(self.backend_module.can_write())

    def get_protocol(self):
        return FILEPROTOCOL

    def get_protocol_full(self):
        return self.get_protocol() + ":"

class GnuCashBasicTest22(GnuCashBasicSetup22, GnuCashBasicTest):
    pass

class GnuCashStartsWithMarkSetup22(GnuCashBasicSetup22,
                                   GnuCashStartsWithMarkSetup):
    def setUp(self):
        GnuCashBasicSetup22.setUp(self)
        self.test_trans = TestTransaction(Decimal(1), BANK_FULL_SPEC,
                                          Decimal(-1), PETTY_CASH_FULL_SPEC )
        self.front_end_id = 1
        self.backend_module.mark_transaction_dirty(
            self.front_end_id, self.test_trans)

class GnuCashStartsWithMarkTests22(GnuCashStartsWithMarkSetup22,
                                   GnuCashStartsWithMarkTests):
    def test_close_account_commod_change_then_flush(self):
        self.backend_module.close()

        self.assertFalse(self.backend_module.transaction_is_clean(
                self.front_end_id) )
        # why not clean, the reason should be checked?

        (s, book, root, accounts) = \
            self.acquire_gnucash_session_book_root_and_accounts()
        assets, bank, petty_cash = accounts[:3]
        
        commod_table = GncCommodityTable(
            instance=gnc_commodity_table_get_table(
                s.book.get_instance()) )
        USD = gnc_commodity_table_lookup(
            commod_table.get_instance(), "ISO4217","USD")

        #commod_table = book.get_table()
        #USD = commod_table.lookup("ISO4217","USD")
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

# remove these from the namespace, we don't want to run thier tests
del GnuCashBasicTest
del GnuCashStartsWithMarkTests

if __name__ == "__main__":
    main()
