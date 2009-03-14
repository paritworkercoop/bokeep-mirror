# python imports
from decimal import Decimal 

# bokeep imports
from module import BackendModule
from bokeep.book_transaction import \
    BoKeepTransactionNotMappableToFinancialTransaction
from bokeep.util import attribute_or_blank

ZERO = Decimal(0)

def get_amount_from_trans_line(trans_line):
    #gnucash imports
    from gnucash import GncNumeric

    return GncNumeric( "%.2f" % trans_line.amount )

def account_from_path(top_account, account_path):
    account, account_path = account_path[0], account_path[1:]
    account = top_account.lookup_by_name(account)
    if len(account_path) > 0 :
        return account_from_path(account, account_path)
    else:
        return account

def get_account_from_trans_line(top_level_account, trans_line):
    assert( hasattr(trans_line, "account_spec") )
    return account_from_path(top_level_account, trans_line.account_spec)

class GnuCash(BackendModule):
    def __init__(self):
        BackendModule.__init__(self)
        self.gnucash_file = ""
        self._v_book_open = False
        self.count = 0

    def openbook_if_not_open(self):
        if not hasattr(self, '_v_book_open') or not self._v_book_open:
            self._v_session = Session("file:" + self.gnucash_file, False)
            self._v_book_open = True
        return True

    def remove_backend_transaction(self, backend_ident):
        if self.openbook_if_not_open():
            pass
        
    def create_backend_transaction(self, fin_trans):
        from gnucash import Session, Transaction, Split, GncNumeric

        if self.openbook_if_not_open():
            description = attribute_or_blank(fin_trans, "description")
            chequenum = attribute_or_blank(fin_trans, "chequenum")
            lines = [ Split(
                    self._v_session.book,
                    get_amount_from_trans_line(trans_line),
                    get_account_from_trans_line(
                        self._v_session.book.get_root_account(),
                        trans_line) )
                      for trans_line in fin_trans.lines ]
            commodtable = GncCommodityTable(
                instance=gnc_commodity_table_get_table(
                    self._v_session.book.get_instance()) )
            CAD = gnc_commodity_table_lookup(
                commodtable.get_instance(), "ISO4217","CAD")

            trans = Transaction(self._v_session.book, CAD, lines)
            trans.SetDescription(
                attribute_or_blank(fin_trans, "description") )
            trans.SetNum(
                attribute_or_blank(fin_trans, "chequenum") )

            for i, split_line in enumerate(lines):
                split_line.SetMemo( attribute_or_blank(fin_trans.lines[i],
                                                       "comment" ) )
            return_value = self.count
            self.count+=1
            return return_value

    def save(self):
        if self.openbook_if_not_open():
            self._v_session.save()

def get_module_class():
    return GnuCash
