# Copyright (C) 2010-2011  ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
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
# Authors: Mark Jenkins <mark@parit.ca>
#          Samuel Pauls <samuel@parit.ca>

# python imports
from decimal import Decimal 
from datetime import date
from glob import glob
from os import remove, kill, system, name
from os.path import exists
from signal import SIGTERM
from time import sleep

# bokeep imports
from plugin import BoKeepBackendException, \
    BoKeepBackendResetException
from session_based_robust_backend_plugin import \
    SessionBasedRobustBackendPlugin
from bokeep.util import attribute_or_blank
from bokeep.gtkutil import gtk_error_message
from bokeep.backend_plugins.gnucash_backend_config import GnuCashConfigDialog

# gnucash imports
from gnucash import Session, Split, GncNumeric, GUID, Transaction, \
    GnuCashBackendException, Account
from gnucash.gnucash_core_c import \
        ERR_FILEIO_BACKUP_ERROR, \
        string_to_guid, \
        guid_to_string # NOTE, this is deprecated and non thread safe
                       # it is probably a very bad idea to be using this
# gtk imports
from gtk import \
    RESPONSE_OK, RESPONSE_CANCEL, ListStore, \
    FILE_CHOOSER_ACTION_OPEN, FileChooserDialog, Dialog, Entry, \
    STOCK_CANCEL, STOCK_OPEN, STOCK_OK, DIALOG_MODAL, EntryCompletion, \
    ComboBoxEntry, MessageDialog, MESSAGE_QUESTION, Button, VBox

SQLITE3 = 'sqlite3'
XML = 'xml'
PROTOCOL_SUFFIX = '://'

# there should be some fairly serrious unit testing for this
def gnc_numeric_from_decimal(decimal_value):
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
                       

def get_amount_from_trans_line(trans_line):
    return gnc_numeric_from_decimal(trans_line.amount)

def account_from_path(gnucash_book, top_account, account_path,
                      original_path=None, create_account_if_missing=False):
    if original_path==None: original_path = account_path
    if not isinstance(account_path, tuple):
        raise BoKeepBackendException(
            "account %s is not a tuple" % str(account_path) )
    account_name, account_path = account_path[0], account_path[1:]
    account = top_account.lookup_by_name(account_name)
    if account.get_instance() == None:
        if create_account_if_missing:
            account = Account(gnucash_book)
            account.SetName(account_name)
            account.SetCommodity(top_account.GetCommodity())
            account.SetType(top_account.GetType())
            top_account.append_child(account)
        else:
            raise BoKeepBackendException(
                "path " + ''.join(original_path) + " could not be found")
    if len(account_path) > 0:
        return account_from_path(gnucash_book, account, account_path,
                                 original_path, create_account_if_missing)
    else:
        return account

def get_account_from_trans_line(gnucash_book, trans_line):
    if not hasattr(trans_line, "account_spec"):
        raise BoKeepBackendException("the gnucash backend needs the "
                                     "optional attribute account_spec "
                                     "to be set" )
    
    create_account_if_missing = (
        False if not hasattr(trans_line, 'create_account_if_missing')
        else trans_line.create_account_if_missing )
        
    return account_from_path(gnucash_book, gnucash_book.get_root_account(),
                             trans_line.account_spec,
                             create_account_if_missing=create_account_if_missing)

def make_new_split(book, amount, account, trans, currency):
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
    if currency.get_fraction() < amount.denom():
        raise BoKeepBackendException(
            "Amount (%s) denominator %s isn't compatible with currency "
            "fraction 1/%s" % (
                amount.num(),
                amount.denom(),
                currency.get_fraction() ) )
    if currency.get_fraction() < account.GetCommoditySCU():
        raise BoKeepBackendException(
            "Account smallest currency unit (SCU) fraction 1/%s doesn't "
            "match currency fraction 1/%s" % (
                account.GetCommoditySCU(),
                currency.get_fraction() ) )
    
    account_commodity = account.GetCommodity()
    if currency.get_mnemonic() != account_commodity.get_mnemonic() or \
            currency.get_namespace() != account_commodity.get_namespace():
        raise BoKeepBackendException(
            "transaction currency and account don't match")
    
    return_value = Split(book)
    return_value.SetValue(amount)
    return_value.SetAmount(amount)
    return_value.SetAccount(account)
    return_value.SetParent(trans)
    return return_value

def call_catch_qofbackend_exception_reraise_important(call_me):
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

class GnuCash(SessionBasedRobustBackendPlugin):
    def __init__(self):
        SessionBasedRobustBackendPlugin.__init__(self)
        self.gnucash_file = None
        self.current_session_error = None

    def can_write(self):
        return SessionBasedRobustBackendPlugin.can_write(self) and \
            self.current_session_error == None

    def remove_backend_transaction(self, backend_ident):
        assert( self.can_write() )
        if self.can_write():
            guid = GUID()
            result = string_to_guid(backend_ident, guid.get_instance())
            assert(result)
            trans = guid.TransLookup(self._v_session_active.book)
            trans.Destroy()

    # this should be overridden with code that actually does a comparision
    #def verify_backend_transaction(self, backend_ident):
    #    return True

    def create_backend_transaction(self, fin_trans):
        description = attribute_or_blank(fin_trans, "description")
        chequenum = attribute_or_blank(fin_trans, "chequenum")
        # important, don't do anything to transaction until splits are
        # added
        trans = Transaction(self._v_session_active.book)
        trans.BeginEdit()
        
        commod_table = self._v_session_active.book.get_table()
        if hasattr(fin_trans, "currency"):
            currency = commod_table.lookup("ISO4217", fin_trans.currency)
        else:
            currency = commod_table.lookup("ISO4217","CAD")

        # create a list of GnuCash splits, set the amount, account,
        # and parent them with the Transaction
        lines = []
        for trans_line in fin_trans.lines:
            try:
                lines.append( make_new_split(
                        self._v_session_active.book,
                        get_amount_from_trans_line(trans_line),
                        get_account_from_trans_line(
                            self._v_session_active.book,
                            trans_line ),
                        trans,
                        currency ) )
            # catch problems fetching the account, currency mismatch
            # with the account, or currency precisions mismatching
            except BoKeepBackendException, e:
                trans.Destroy() # undo what we have done
                raise e # and re-raise the exception

        trans.SetCurrency(currency)

        if trans.GetImbalanceValue().num() != 0:
            trans.Destroy() # undo what we have done
            trans.CommitEdit()
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
        # not checking for gnucash_file == None contributed to bug #33616
        #
        # The gnucash python bindings implementation of Session just does
        # nothing if you pass it book_uri == None
        # It probably behaves that way so you can have a way to init the
        # Session instance and not do anything else -- as the default is
        # sure pretty active in terms of calling several undering functions
        #
        # so passing None to that argument and expecting Session to
        # throw an Exception was definitely the wrong expectation
        #
        # The only reason that ever worked was because
        # Session.save() was being called shortly after
        # open_session() here, and would get angry, and the gnucash backend
        # would immediately close down the session
        #
        # Not so as of GnuCash 2.4.6, and possibly some of the versions
        # after 2.4.2 ... Session.save would just do nothing when
        # initialized with book_uri=None...
        #
        # by checking for this and refusing right away to open the
        # session, we no longer rely on Session.save() later to tell
        # us that None is a stupid value
        if self.gnucash_file == None:
            self.current_session_error = "no gnucash file selected"
            return None
        
        # If the GnuCash books are locked...
        gnucash_lock = self.gnucash_file[6:] + '.LCK'
        if exists(gnucash_lock):
            if name == 'posix':
                # Attempt to get GnuCash's process ID.
                pid_file = '/tmp/gnucashpid'
                system('pidof gnucash > ' + pid_file)
                f = open(pid_file, 'r')
                line = f.readline()
                # If there are multiple GnuCash instances, "pidof gnucash" will
                # return something like "9000 9001".
                multiple_gnucash_instances = line.find(' ') >= 0
                if line == '' or multiple_gnucash_instances:
                    pid = 0
                else: # If there's exactly one instance of GnuCash running...
                    pid = int(line)
                f.close()
                remove(pid_file)
                
                if pid == 0:
                    OTHER_PROGRAM = 'another accounting program'
                    OTHER_PROGRAM2 = 'the other accounting program'
                    DANGEROUS_OPTION = 'Risk corruption of the accounting ' + \
                        'resource by having BoKeep use it in parallel!'
                else:
                    OTHER_PROGRAM = 'GnuCash'
                    OTHER_PROGRAM2 = OTHER_PROGRAM
                    DANGEROUS_OPTION = 'Terminating GnuCash and lose its ' + \
                                       'unsaved changes!'
                    
                md = MessageDialog(type = MESSAGE_QUESTION,
                    message_format = "BoKeep is waiting to save double " +
                    "entry accounting transactions because " + OTHER_PROGRAM +
                    " is busy with the accounting " +
                    "resource.  It's unsafe for two programs to work " +
                    "with the accounting resource in parallel!  " +
                    "How do you wish to proceed?")
                
                # Add some response buttons in the standard way,
                # which also sets up non-obtrusive signals.
                save_later_button = Button(
                    "I've closed " + OTHER_PROGRAM2 + " or wish to " +
                    "have BoKeep update the accounting resource later.")
                RESPONSE_SAVE_LATER = 1
                md.add_action_widget(save_later_button, RESPONSE_SAVE_LATER)
                save_now_button = Button(DANGEROUS_OPTION)
                RESPONSE_SAVE_NOW = 2
                md.add_action_widget(save_now_button, RESPONSE_SAVE_NOW)
                
                # Reparent the buttons to a vbox so that their layout is
                # vertical instead of the standard horizontal.
                # (Horizontal action buttons aren't suited to the complexity of
                # the user's response.  Sure the response could first be
                # summarised in the above paragraph and the user provided Yes/No
                # buttons, but that's more lingually complicated for the user
                # and the situation demands a clear understanding.)
                vbox = VBox()
                SPACING_BETWEEN_BUTTONS = 8
                vbox.set_spacing(SPACING_BETWEEN_BUTTONS)
                md.action_area.pack_start(vbox)
                save_later_button.reparent(vbox)
                save_now_button.reparent(vbox)
                
                md.show_all()
                r = md.run()
                md.destroy()
                if r == RESPONSE_SAVE_NOW:
                    if pid != 0:
                        # As of GnuCash 2.4.6, GnuCash seems to not handle
                        # signals so it can't be expected to save changes upon
                        # exit.
                        kill(pid, SIGTERM)
                    
                    # As of GnuCash 2.4.6, GnuCash doesn't remove locks
                    # when terminated by signal.
                    remove(gnucash_lock)

        # but this try/except is fine for other bogus values
        # of self.gnucash_file/book_uri
        try:
            session = Session(self.gnucash_file, is_new=False)
            self.current_session_error = None
        except GnuCashBackendException, e:
            session = None
            self.current_session_error = str(e)
        return session

    def save(self):
        try:
            call_catch_qofbackend_exception_reraise_important(
                self._v_session_active.save)
        # this should be a little more refined, the session isn't neccesarilly
        # dead... or had end() not be callable, we already ignore the
        # couldn't make a backup exception
        except GnuCashBackendException, e:
            self.current_session_error = str(e)
            if hasattr(self, '_v_session_active'):
                self._v_session_active.destroy()
                del self._v_session_active
            raise BoKeepBackendResetException(
                "gnucash save failed " + str(e))
        return None

    def close(self, close_reason='reset because close() was called'):
        if self.can_write():
            #if self.has_active_session_attr():
            self._v_session_active.end()
            self._v_session_active.destroy()
        if self.current_session_error != None:
            close_reason = "close() called because gnucash session failed " + \
                self.current_session_error 
        SessionBasedRobustBackendPlugin.close(self, close_reason)

    def configure_backend(self, parent_window=None):
        cd = GnuCashConfigDialog()
        # At least when a new account is created and a backend immediately
        # selected, self.gnucash_file is of type None.
        if isinstance(self.gnucash_file, str):
            gnucash_filename = self.gnucash_file[6:]
            cd.set_book_filename(gnucash_filename)
        cd.run()
        gnucash_filename = cd.get_book_filename()
        self.setattr('gnucash_file', 'xml' + '://' + gnucash_filename)

    def get_account_names(self, account, names = None, prefix = ''):
        # Initialise the default value of names.
        # Remember that Python only initialises a default parameter once upon
        # execution of a respective def statement.  Thus a mutable default
        # parameter can be changed on an invocation of the respective function
        # and reused on subsequent invocations without being reset, unless we
        # reset it like this specifically...
        if names is None:
            names = []
        
        # Get the name of the current account.
        if not account.is_root():
            if not account.GetPlaceholder():
                names.append(prefix + account.name)
            prefix += account.name + ':'
        
        # Iterate through the account's children.
        for child in account.get_children():
            child = Account(instance = child)
            names = self.get_account_names(child, names, prefix)
            
        return names
    
    def backend_account_dialog(self, parent_window=None):
        # An open session is required to get the list of back-end accounts.
        self.open_session_and_retain()

        if not self.can_write():
            gtk_error_message("The gnucash file %s is not available due to %s" %
                              (self.gnucash_file, self.current_session_error) )
            return None, ''

        dia = Dialog("Please enter a gnucash account",
                     parent_window, DIALOG_MODAL,
                     (STOCK_OK, RESPONSE_OK,
                      STOCK_CANCEL, RESPONSE_CANCEL ) )
        dia.set_response_sensitive(RESPONSE_OK, False)
        
        # Setup auto-complete for the entry widget.
        completion = EntryCompletion()
        completion.set_minimum_key_length(0)
        list_store = ListStore(str)
        names = self.get_account_names(
                    self._v_session_active.get_book().get_root_account())
        for name in names:
            list_store.append([name])
        completion.set_model(list_store)
        completion.set_text_column(0)
        
        # Create an account entry widget.
        account_entry = ComboBoxEntry(list_store) # drop down list
        account_entry.child.set_completion(completion) # auto complete list
        account_entry.child.set_width_chars(60)
        account_entry.connect('changed', self.__on_account_entry_changed, dia)
        dia.vbox.pack_start(account_entry)
        
        dia.vbox.show_all()
        result = dia.run()
        account_text = account_entry.child.get_text()
        dia.destroy()
        if result == RESPONSE_OK:
            return tuple(account_text.split(':')), account_text
        else:
            return None, ''

    def __on_account_entry_changed(self, combobox, dialog):
        # Can we find the account entered in the combo box?
        text = combobox.child.get_text()
        model = combobox.get_model()
        iter = model.get_iter_first()
        while iter != None and model.get_value(iter, 0) != text:
            iter = model.iter_next(iter)
        if iter != None and model.get_value(iter, 0) == text:
            found_account = True
        else:
            found_account = False
        
        # If so, enable OK.
        dialog.set_response_sensitive(RESPONSE_OK, found_account)

def get_plugin_class():
    return GnuCash