# python imports
from decimal import Decimal 
from datetime import date

# bokeep imports
from module import BackendModule
from bokeep.book_transaction import \
    BoKeepTransactionNotMappableToFinancialTransaction
from bokeep.util import attribute_or_blank

ZERO = Decimal(0)

def gnc_numeric_from_string(numeric_string):
    from gnucash import GncNumeric
    from gnucash.gnucash_core_c import string_to_gnc_numeric
    numeric_string = numeric_string.strip() # murder whitespace

    if len(numeric_string) > 0:
        # if there is a decimal point get rid of it
        if '.' in numeric_string:
            # get the parts left and right of the decimal point
            left_of_decimal, right_of_decimal = numeric_string.split('.')

            negate = ''

            if len(left_of_decimal) > 0:
                if left_of_decimal[0] == '-':
                    negate = '-'
                    left_of_decimal = left_of_decimal[1:]

                left_of_decimal = int(left_of_decimal)
                if left_of_decimal == 0:
                    left_of_decimal = ''
                else:
                    left_of_decimal = str(left_of_decimal)



            # the string now consists of the left part, right part,
            # /1 and and apropriate number of 0's
            numeric_string = '%s%s%s/1%s' % (
                negate,
                left_of_decimal,
                right_of_decimal,
                # put len(right_of_decimal) 0's in the denominator,
                # eg 10.1 -> 101/10,
                # len(right_of_decimal) == 1, (one zero)
                # eg 10.10 -> 1010/100,
                # len(right_of_decimal) == 2, (two zeros)
                # eg 10.100 -> 10100/1000
                # len(right_of_decimal) == 3, (three zeros)
                '0'*len(right_of_decimal) ) 
    else:
        numeric_string = '0/1'

    if '/' not in numeric_string:
        numeric_string += '/1'

    gncnumeric = GncNumeric()
    convert_success = string_to_gnc_numeric(
        numeric_string,
        gncnumeric.get_instance()
        )
    assert( convert_success )
    return gncnumeric

def get_amount_from_trans_line(trans_line):
    return gnc_numeric_from_string(str(trans_line.amount))

def account_from_path(top_account, account_path, original_path=None):
    if original_path==None: original_path = account_path
    account, account_path = account_path[0], account_path[1:]
    account = top_account.lookup_by_name(account)
    if account.get_instance() == None:
        raise BoKeepTransactionNotMappableToFinancialTransaction(
            "path" + ''.join(original_path) + " could not be found")
    if len(account_path) > 0 :
        return account_from_path(account, account_path, original_path)
    else:
        return account

def get_account_from_trans_line(top_level_account, trans_line):
    assert( hasattr(trans_line, "account_spec") )
    return account_from_path(top_level_account, trans_line.account_spec)

def make_new_split(book, amount, account, trans, currency):
    from gnucash import Split
    from gnucash.gnucash_core_c import gnc_commodity_get_fraction, \
        xaccAccountGetCommodity, gnc_commodity_get_mnemonic, \
        gnc_commodity_get_namespace
        
    if gnc_commodity_get_fraction(currency) != amount.denom():
        raise BoKeepTransactionNotMappableToFinancialTransaction(
            "Amount denominator doesn't match currency fraction")
    if gnc_commodity_get_fraction(currency) != account.GetCommoditySCU():
        raise BoKeepTransactionNotMappableToFinancialTransaction(
            "Account smallest currency unit (SCU) doesn't match currency "
            "fraction")
    account_inst = account.get_instance()
    if \
            gnc_commodity_get_mnemonic(currency) == \
            gnc_commodity_get_mnemonic(xaccAccountGetCommodity(account_inst)) \
            and \
            gnc_commodity_get_namespace(currency) == \
            gnc_commodity_get_namespace(xaccAccountGetCommodity(account_inst)):
        raise BoKeepTransactionNotMappableToFinancialTransaction(
            "transaction currency and account don't match")
    
    return_value = Split(book)
    return_value.SetValue(amount)
    return_value.SetAmount(amount)
    return_value.SetAccount(account)
    return_value.SetParent(trans)
    return return_value


class GnuCash(BackendModule):
    def __init__(self):
        BackendModule.__init__(self)
        self.gnucash_file = None
        self._v_book_open = False

    def can_write(self):
        return self.openbook_if_not_open()

    def openbook_if_not_open(self):
        from gnucash import Session
        if self.gnucash_file == None:
            return False
        if not hasattr(self, '_v_book_open') or not self._v_book_open:
            self._v_session = Session("file:" + self.gnucash_file, False)
            self._v_book_open = True
        return True

    def remove_backend_transaction(self, backend_ident):
        from gnucash import GUID
        from gnucash.gnucash_core_c import string_to_guid
        assert( self.can_write() )
        if self.can_write():
            guid = GUID()
            result = string_to_guid(backend_ident, guid.get_instance())
            assert(result)
            trans = guid.TransLookup(self._v_session.book)
            trans.Destroy()
        
    def create_backend_transaction(self, fin_trans):
        from gnucash import Transaction, GncCommodityTable
        from gnucash.gnucash_core_c import \
            gnc_commodity_table_get_table, gnc_commodity_table_lookup, \
            guid_to_string # NOTE, this is deprecated and non thread safe
                           # it is probably a very bad idea to be using this
        
        if self.openbook_if_not_open():
            description = attribute_or_blank(fin_trans, "description")
            chequenum = attribute_or_blank(fin_trans, "chequenum")
            # important, don't do anything to transaction until splits are
            # added
            trans = Transaction(self._v_session.book)

            
            commodtable = GncCommodityTable(
                instance=gnc_commodity_table_get_table(
                    self._v_session.book.get_instance()) )
            CAD = gnc_commodity_table_lookup(
                commodtable.get_instance(), "ISO4217","CAD")

            # create a list of GnuCash splits, set the amount, account,
            # and parent them with the Transaction
            lines = []
            for trans_line in fin_trans.lines:
                try:
                    lines.append( make_new_split(
                            self._v_session.book,
                            get_amount_from_trans_line(trans_line),
                            get_account_from_trans_line(
                                self._v_session.book.get_root_account(),
                                trans_line ),
                            trans,
                            CAD ) )
                # catch problems fetching the account, currency mismatch
                # with the account, or currency precisions mismatching
                except BoKeepTransactionNotMappableToFinancialTransaction, e:
                    trans.Destory() # undo what we have done
                    raise e # and re-raise the exception
                    
            trans.SetCurrency(CAD)

            # if there's an imbalance
            if trans.GetImbalance().num() != 0:
                trans.Destory() # undo what we have done
                raise BoKeepTransactionNotMappleToFinancialTransaction(
                    "transaction doesn't balance")

            trans.SetDescription(
                attribute_or_blank(fin_trans, "description") )
            trans.SetNum(
                str( attribute_or_blank(fin_trans, "chequenum") ) )
            trans_date = attribute_or_blank(fin_trans, "trans_date")
            if not isinstance(trans_date, str):
                trans.SetDatePostedTS(trans_date)
            trans.SetDateEnteredTS(date.today())

            for i, split_line in enumerate(lines):
                split_line.SetMemo( attribute_or_blank(fin_trans.lines[i],
                                                       "line_memo" ) )
            trans_guid = trans.GetGUID()
            # guid_to_string is deprecated and string safe, and it owns the
            # value it returns.
            # copy with list and str.join to be sure we have a true copy
            return ''.join(list( guid_to_string(trans_guid.get_instance()) ) )

    def save(self):
        if self.openbook_if_not_open():
            self._v_session.save()

    def close(self):
        if hasattr(self, '_v_book_open') and self._v_book_open:
            self._v_session.end()

def get_module_class():
    return GnuCash
