# python imports
from decimal import Decimal 

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

def make_new_split(book, amount, account, trans):
    from gnucash import Split
    return_value = Split( book )
    return_value.SetValue(amount)
    return_value.SetAmount(amount)
    return_value.SetAccount(account)
    return_value.SetParent(trans)
    return return_value


class GnuCash(BackendModule):
    def __init__(self):
        BackendModule.__init__(self)
        self.gnucash_file = ""
        self._v_book_open = False
        self.count = 0

    def can_write(self):
        return self.openbook_if_not_open()

    def openbook_if_not_open(self):
        from gnucash import Session
        if not hasattr(self, '_v_book_open') or not self._v_book_open:
            self._v_session = Session("file:" + self.gnucash_file, False)
            self._v_book_open = True
        return True

    def remove_backend_transaction(self, backend_ident):
        if self.openbook_if_not_open():
            pass
        
    def create_backend_transaction(self, fin_trans):
        from gnucash import Transaction, GncCommodityTable
        from gnucash.gnucash_core_c import \
            gnc_commodity_table_get_table, gnc_commodity_table_lookup
        
        if self.openbook_if_not_open():
            description = attribute_or_blank(fin_trans, "description")
            chequenum = attribute_or_blank(fin_trans, "chequenum")
            # important, don't do anything to transaction until splits are
            # added
            trans = Transaction(self._v_session.book)

            # create a list of GnuCash splits, set the amount, account,
            # and parent them with the Transaction
            lines = [ make_new_split(
                    self._v_session.book,
                    get_amount_from_trans_line(trans_line),
                    get_account_from_trans_line(
                        self._v_session.book.get_root_account(),
                        trans_line),
                    trans )
                      for trans_line in fin_trans.lines ]
            
            commodtable = GncCommodityTable(
                instance=gnc_commodity_table_get_table(
                    self._v_session.book.get_instance()) )
            CAD = gnc_commodity_table_lookup(
                commodtable.get_instance(), "ISO4217","CAD")
            
            trans.SetCurrency(CAD)
            trans.SetDescription(
                attribute_or_blank(fin_trans, "description") )
            trans.SetNum(
                str( attribute_or_blank(fin_trans, "chequenum") ) )

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
