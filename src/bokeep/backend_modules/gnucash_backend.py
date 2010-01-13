# python imports
from decimal import Decimal 
from datetime import date

# bokeep imports
from module import BackendModule
from bokeep.book_transaction import \
    BoKeepTransactionNotMappableToFinancialTransaction
from bokeep.util import attribute_or_blank


# there should be some fairly serrious unit testing for this
def gnc_numeric_from_decimal(decimal_value):
    from gnucash import GncNumeric
    sign, digits, exponent = decimal_value.as_tuple()

    # convert decimal digits to a fractional numerator
    # equivlent to
    # numerator = int(''.join(digits))
    # but without the wated conversion to string and back,
    # this is probably the same algorithm int() uses
    numerator = 0
    TEN = int(Decimal(0).radix()) # this is always 10
    numerator_place_value = 1
    # add each digit to the final value multiplied by the place value
    # from least significant to most sigificant
    for i in xrange(len(digits)-1,-1,-1):
        numerator += digits[i] * numerator_place_value
        numerator_place_value *= TEN

    if decimal_value.is_signed():
        numerator = -numerator

    # if the exponent is negative, we use it to set the denominator
    if exponent < 0 :
        denominator = TEN ** (-exponent)
    # if the exponent isn't negative, we bump up the numerator
    # and set the denominator to 1
    else:
        numerator *= TEN ** exponent
        denominator = 1

    return GncNumeric(numerator, denoninator)
                       

def get_amount_from_trans_line(trans_line):
    return gnc_numeric_from_decimal(trans_line.amount)

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

    # the fraction tests used to be !=, but it was realized that
    # there isn't a reason to be concerned if the amount denominator is
    # smaller or equal to the currency fraction,
    # e.g. if the amount is x/10 or x/100, and the currency fraction is
    # x/100, there isn't a problem, because you don't lose information
    # if you make amount into y/100 (y=10x [first example] or y=x
    # [second example]
    #
    # But, there is an assumption of that sort of convertability
    # always being possible for the conditions given for tolerance here
    #
    # if you end up with fractions like x/7 you can't exactly make them
    # into y/5 or z/9, and unfortunalty these checks won't catch that
    if gnc_commodity_get_fraction(currency) < amount.denom():
        raise BoKeepTransactionNotMappableToFinancialTransaction(
            "Amount denominator %s isn't compatible with currency "
            "fraction 1/%s" % (
                amount.denom(),
                gnc_commodity_get_fraction(currency) ) )
    if gnc_commodity_get_fraction(currency) < account.GetCommoditySCU():
        raise BoKeepTransactionNotMappableToFinancialTransaction(
            "Account smallest currency unit (SCU) fraction 1/%s doesn't "
            "match currency fraction 1/%s" % (
                account.GetCommoditySCU(),
                gnc_commodity_get_fraction(currency) ) )
    
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
