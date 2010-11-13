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

# python imports
from decimal import Decimal 
from datetime import date
from glob import glob
from os import remove
from time import sleep

# bokeep imports
from module import BoKeepBackendException, \
    BoKeepBackendResetException
from session_based_robust_backend_module import \
    SessionBasedRobustBackendModule
from bokeep.util import attribute_or_blank

# gtk imports
from gtk import \
    RESPONSE_OK, RESPONSE_CANCEL, \
    FILE_CHOOSER_ACTION_OPEN, FileChooserDialog, \
    STOCK_CANCEL, STOCK_OPEN

# there should be some fairly serrious unit testing for this
def gnc_numeric_from_decimal(decimal_value):
    # a kludge because we can't import at the top!
    from gnucash import GncNumeric
    # this is the only difference from the GnuCash (24) backend plugin
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

    return GncNumeric(numerator, denominator)
                       

# this is identical to the function from the GnuCash (24) backend plugin
# too bad we can't just import it, can't because GnuCash (24) backend plugin
# does imports of the gnucash python bindings at the top, which break in 2.2
def get_amount_from_trans_line(trans_line):
    return gnc_numeric_from_decimal(trans_line.amount)

# this is identical to the function from the GnuCash (24) backend plugin
# too bad we can't just import it, can't because GnuCash (24) backend plugin
# does imports of the gnucash python bindings at the top, which break in 2.2
def account_from_path(top_account, account_path, original_path=None):
    if original_path==None: original_path = account_path
    account, account_path = account_path[0], account_path[1:]
    account = top_account.lookup_by_name(account)
    if account.get_instance() == None:
        raise BoKeepBackendException(
            "path " + ''.join(original_path) + " could not be found")
    if len(account_path) > 0 :
        return account_from_path(account, account_path, original_path)
    else:
        return account

# this is identical to the function from the GnuCash (24) backend plugin
# too bad we can't just import it, can't because GnuCash (24) backend plugin
# does imports of the gnucash python bindings at the top, which break in 2.2
def get_account_from_trans_line(top_level_account, trans_line):
    if not hasattr(trans_line, "account_spec"):
        raise BoKeepBackendException("the gnucash backend needs the "
                                     "optional attribute account_spec "
                                     "to be set" )
    return account_from_path(top_level_account, trans_line.account_spec)

def make_new_split(book, amount, account, trans, currency):
    # a kludge because we can't import at the top!
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
    
    # this is different from how its done in GnuCash (24) backend plugin
    if gnc_commodity_get_fraction(currency) < amount.denom():
        raise BoKeepBackendException(
            "Amount (%s) denominator %s isn't compatible with currency "
            "fraction 1/%s" % (
                amount.num(),
                amount.denom(),
                currency.get_fraction() ) )
    # this is different from how its done in GnuCash (24) backend plugin
    if gnc_commodity_get_fraction(currency) < account.GetCommoditySCU():
        raise BoKeepBackendException(
            "Account smallest currency unit (SCU) fraction 1/%s doesn't "
            "match currency fraction 1/%s" % (
                account.GetCommoditySCU(),
                gnc_commodity_get_fraction(currency) ) )
    
    # this is different from how its down in GnuCash (24) backend plugin
    account_inst = account.get_instance()
    if \
            gnc_commodity_get_mnemonic(currency) != \
            gnc_commodity_get_mnemonic(xaccAccountGetCommodity(account_inst)) \
            or \
            gnc_commodity_get_namespace(currency) != \
            gnc_commodity_get_namespace(xaccAccountGetCommodity(account_inst)):
        raise BoKeepBackendException(
            "transaction currency and account don't match")
    # the above is the last difference in this func compared to GnuCash (24)
    # backend plugin

    return_value = Split(book)
    return_value.SetValue(amount)
    return_value.SetAmount(amount)
    return_value.SetAccount(account)
    return_value.SetParent(trans)
    return return_value

def call_catch_qofbackend_exception_reraise_important(call_me):
    # import kludge
    from gnucash import GnuCashBackendException
    from gnucash.gnucash_core_c import ERR_FILEIO_BACKUP_ERROR
    # above is only difference with GnuCash (24) backend plugin
    while True:
        try:
            call_me()
        except GnuCashBackendException, e:
            # ignore a backup file error, they happen normally when save()
            # is called frequently because the file names on the backup files
            # end up having the same timestamp
            # but we have learned that the cal to save doesn't actually
            # finish when this error happens, so we have a while True
            # loop here and a 1 second delay to do it over and over again
            if len(e.errors) == 1 and e.errors[0] == ERR_FILEIO_BACKUP_ERROR:
                sleep(2)
            else:
                raise e
        else:
            break # break while

class GnuCash22(SessionBasedRobustBackendModule):
    # not changed from GnuCash (24) backend plugin, too bad the import
    # kludge prevents us from using inheritance or something common
    def __init__(self):
        SessionBasedRobustBackendModule.__init__(self)
        self.gnucash_file = None
        self.current_session_error = None

    # not changed from GnuCash (24) backend plugin, too bad the import
    # kludge prevents us from using inheritance or something common
    def can_write(self):
        return SessionBasedRobustBackendModule.can_write(self) and \
            self.current_session_error == None

    def remove_backend_transaction(self, backend_ident):
        # this is a kludge to avoid importing at the top to avoid stack
        # overflow issues... uuug!
        from gnucash import GUID
        from gnucash.gnucash_core_c import string_to_guid
        # this is the only change from the GnuCash (24) backend plugin

        assert( self.can_write() )
        if self.can_write():
            guid = GUID()
            result = string_to_guid(backend_ident, guid.get_instance())
            assert(result)
            trans = guid.TransLookup(self._v_session_active.book)
            trans.Destroy()

    def create_backend_transaction(self, fin_trans):
        # this is a kludge to avoid importing at the top to avoid stack
        # overflow issues... uuug!
        from gnucash import Transaction, GncCommodityTable
        from gnucash.gnucash_core_c import \
            gnc_commodity_table_get_table, gnc_commodity_table_lookup, \
            guid_to_string # NOTE, this is deprecated and non thread safe
                           # it is probably a very bad idea to be using this
        
        description = attribute_or_blank(fin_trans, "description")
        chequenum = attribute_or_blank(fin_trans, "chequenum")
        # important, don't do anything to transaction until splits are
        # added
        trans = Transaction(self._v_session_active.book)
        trans.BeginEdit()
        
        # This is how its done in the GnuCash (24) backend plugin
        #commod_table = self._v_session_active.book.get_table()
        #CAD = commod_table.lookup("ISO4217","CAD")
        # this is the oldschool 2.2 bindings way of getting a currency
        commod_table = GncCommodityTable(
            instance=gnc_commodity_table_get_table(
                self._v_session_active.book.get_instance()) )
        CAD = gnc_commodity_table_lookup(
            commod_table.get_instance(), "ISO4217","CAD")

        # create a list of GnuCash splits, set the amount, account,
        # and parent them with the Transaction
        lines = []
        for trans_line in fin_trans.lines:
            try:
                lines.append( make_new_split(
                        self._v_session_active.book,
                        get_amount_from_trans_line(trans_line),
                        get_account_from_trans_line(
                            self._v_session_active.book.get_root_account(),
                            trans_line ),
                        trans,
                        CAD ) )
            # catch problems fetching the account, currency mismatch
            # with the account, or currency precisions mismatching
            except BoKeepBackendException, e:
                trans.Destroy() # undo what we have done
                raise e # and re-raise the exception

        trans.SetCurrency(CAD)

        # was trans.GetImbalanceValue().num() in GnuCash (24) backend plugin
        if trans.GetImbalance().num() != 0:
            trans.Destroy() # undo what we have done
            trans.xaccTransCommitEdit()
            raise BoKeepBackendException(
                "transaction doesn't balance")

        trans.SetDescription(
            attribute_or_blank(fin_trans, "description") )
        trans.SetNum(
            str( attribute_or_blank(fin_trans, "chequenum") ) )
        trans_date = attribute_or_blank(fin_trans, "trans_date")
        if not isinstance(trans_date, str):
            trans.SetDatePostedTS(trans_date)
        trans.SetDateEnteredTS(date.today())
        trans.CommitEdit()

        for i, split_line in enumerate(lines):
            split_line.SetMemo( attribute_or_blank(fin_trans.lines[i],
                                                   "line_memo" ) )
        trans_guid = trans.GetGUID()
        # guid_to_string is deprecated and string safe, and it owns the
        # value it returns.
        # copy with list and str.join to be sure we have a true copy
        return ''.join(list( guid_to_string(trans_guid.get_instance()) ) )

    def open_session(self):
        # import kludge
        from gnucash import Session, GnuCashBackendException
        # this is the only difference from GnuCash (24) backend plugin
        # and note that with 2.2 that "file:" needs to be there in
        # self.gnucash_file instead of sqllite3: or xml:
        # e.g. file:/blah.gnucash
        try:
            session = Session(self.gnucash_file, False)
            self.current_session_error = None
        except GnuCashBackendException, e:
            session = None
            self.current_session_error = e.message
        return session

    def save(self):
        from gnucash import GnuCashBackendException
        try:
            call_catch_qofbackend_exception_reraise_important(
                self._v_session_active.save)
        # this should be a little more refined, the session isn't neccesarilly
        # dead... or had end() not be callable, we already ignore the
        # couldn't make a backup exception
        except GnuCashBackendException, e:
            self.current_session_error = e.message
            if hasattr(self, '_v_session_active'):
                self._v_session_active.destroy()
                del self._v_session_active
            raise BoKeepBackendResetException(
                "gnucash save failed " + e.message)
        return None

    def close(self, close_reason='reset because close() was called'):
        if self.can_write():
            #if self.has_active_session_attr():
            self._v_session_active.end()
            self._v_session_active.destroy()
        if self.current_session_error != None:
            close_reason = "close() called because gnucash session failed " + \
                self.current_session_error 
        SessionBasedRobustBackendModule.close(self, close_reason)

    def configure_backend(self, parent_window=None):
        fcd = FileChooserDialog(
            "Where is the gnucash file?",
            parent_window,
            FILE_CHOOSER_ACTION_OPEN,
            (STOCK_CANCEL, RESPONSE_CANCEL, STOCK_OPEN, RESPONSE_OK) )
        fcd.set_modal(True)
        result = fcd.run()
        gnucashfile_path = fcd.get_filename()
        fcd.destroy()
        if result == RESPONSE_OK and gnucashfile_path != None:
            self.setattr('gnucash_file', 'file' + ':' + gnucashfile_path)
    def backend_account_dialog(self, parent_window=None):
        dia = Dialog("Please enter a gnucash account",
                     parent_window, DIALOG_MODAL,
                     (STOCK_OK, RESPONSE_OK,
                      STOCK_CANCEL, RESPONSE_CANCEL ) )
        account_entry = Entry()
        account_entry.set_width_chars(60)
        dia.vbox.pack_start(account_entry)
        account_entry.show()
        dia.vbox.show_all()
        result = dia.run()
        account_text = account_entry.get_text()
        dia.destroy()
        if result == RESPONSE_OK:
            return tuple(account_text.split(':')), account_text
        else:
            return None, ''

def get_module_class():
    return GnuCash22
