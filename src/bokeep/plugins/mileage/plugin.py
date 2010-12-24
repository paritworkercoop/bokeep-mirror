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

from persistent import Persistent

from decimal import Decimal, InvalidOperation
from datetime import datetime, date
from os.path import abspath, dirname, join, exists

from gtk import RESPONSE_OK

from bokeep.gui.gladesupport.GladeWindow import GladeWindow
from bokeep.book_transaction import \
    Transaction, FinancialTransaction, FinancialTransactionLine, \
    BoKeepTransactionNotMappableToFinancialTransaction
from bokeep.gui.gladesupport.glade_util import \
    load_glade_file_get_widgets_and_connect_signals


ZERO = Decimal(0)
ONE = Decimal(1)
NEG_1 = Decimal(-1)
TWO_PLACES = Decimal('0.01')

def get_mileage_glade_file():
    import plugin as plugin_mod
    return join( dirname( abspath( plugin_mod.__file__ ) ),
                 'mileage.glade')

class MileageTransaction(Transaction):
    def __init__(self, mileage_plugin):
        Transaction.__init__(self, mileage_plugin)
        self.distance = Decimal(ZERO)
        self.trans_date = datetime.today()

    def make_trans_line(self, account_spec, negate=False):
        amount = (self.get_distance() * \
            self.associated_plugin.distance_multiplier).quantize(
            TWO_PLACES)
        if negate:
            amount = -amount
        return_value =  FinancialTransactionLine(amount)
        return_value.account_spec = account_spec
        return return_value

    def get_financial_transactions(self):
        # you should throw BoKeepTransactionNotMappableToFinancialTransaction
        # under some conditions
        if isinstance(self.get_distance(), Decimal):
            return_value = FinancialTransaction(
                (self.make_trans_line(
                        self.associated_plugin.get_debit_account() ),
                 self.make_trans_line(
                        self.associated_plugin.get_credit_account(), True) )
                )
            return_value.description = 'mileage'
            return_value.trans_date = self.trans_date
            return (return_value,)
        else:
            raise BoKeepTransactionNotMappableToFinancialTransaction(
                "the number of miles is not specified")

    def get_distance(self):
        return self.distance

    def set_distance(self, distance):
        self.distance = distance

def mileage_editable_editor(
    trans, transid, plugin, gui_parent, change_register_function):
    editor = mileage_entry(trans, transid, plugin, gui_parent,
                           change_register_function)
    return editor

MILEAGE_CODE = 0

class MileagePlugin(Persistent):
    def __init__(self):
        self.debit_account = self.credit_account = None
        self.debit_account_str =  self.credit_account_str = ""
        self.distance_multiplier = ONE
        self.trans_registry = {}

    def get_debit_account(self):
        return self.debit_account

    def get_credit_account(self):
        return self.credit_account   

    def run_configuration_interface(
        self, parent_window, backend_account_fetch):
        dia = MileageConfigDialog(parent_window, backend_account_fetch,
                                  self)
        dia.run()

    def register_transaction(self, front_end_id, trust_trans):
        assert( not self.has_transaction(front_end_id) )
        self.trans_registry[front_end_id] = trust_trans

    def remove_transaction(self, front_end_id):
        del self.trans_registry[front_end_id]

    def has_transaction(self, trans_id):
        return trans_id in self.trans_registry
        
    @staticmethod
    def get_transaction_type_codes():
        return (MILEAGE_CODE,)

    @staticmethod
    def get_transaction_type_from_code(code):
        assert(code == MILEAGE_CODE)
        return MileageTransaction

    @staticmethod
    def get_transaction_type_pulldown_string_from_code(code):
        assert(code == MILEAGE_CODE)
        return "Mileage"
        
    @staticmethod
    def get_transaction_edit_interface_hook_from_code(code):
        return mileage_editable_editor

class mileage_entry(GladeWindow):
    def __init__(self, trans, transid, plugin, gui_parent,
                 change_register_function):
        from plugin import get_mileage_glade_file
        self.gui_built = False
        GladeWindow.__init__(
            self, get_mileage_glade_file(),
            'window1', ('window1', 'amount_entry', 'vbox1', 'calendar1'),
            ('on_window_destroy', 'on_amount_entry_changed',
             'on_cal_date_changed') )

        self.trans = trans
        self.widgets['calendar1'].select_month(
            self.trans.trans_date.month-1, self.trans.trans_date.year)
        self.widgets['calendar1'].select_day(self.trans.trans_date.day)
        
        if isinstance(self.trans.get_distance(), Decimal):
            self.widgets['amount_entry'].set_text(
                str(self.trans.get_distance()) )

        self.plugin = plugin
        self.change_register_function = change_register_function
        
        if not gui_parent == None:
            self.widgets['vbox1'].reparent(gui_parent)
        self.top_window.hide()
        self.gui_built = True

    def detach(self):
        self.widgets['vbox1'].reparent(self.top_window)

    def on_amount_entry_changed(self, *args):
        # skip this if being set by code and not user at init
        if not self.gui_built: return
        try:
            self.trans.set_distance(
                Decimal(self.widgets['amount_entry'].get_text()))
        except InvalidOperation: pass
        else:
            self.change_register_function()

    def on_cal_date_changed(self, *args):
        # skip this if being set by code and not user at init
        if not self.gui_built: return
        (year, month, day) = self.widgets['calendar1'].get_date()
        self.trans.trans_date = \
            date(year, month+1, day)
        self.change_register_function()

    
class MileageConfigDialog(object):
    def __init__(self, parent_window, backend_account_fetch, plugin):
        load_glade_file_get_widgets_and_connect_signals(
            get_mileage_glade_file(), 'dialog1', self, self)
        self.backend_account_fetch = backend_account_fetch
        self.plugin = plugin
        
        self.set_debit_account(self.plugin.get_debit_account(),
                               self.plugin.debit_account_str )
        self.set_credit_account(self.plugin.get_credit_account(),
                                self.plugin.credit_account_str )
        if isinstance(self.plugin.distance_multiplier, Decimal):
            self.distance_multiple_entry.set_text(
                str(self.plugin.distance_multiplier) )
                            
        if parent_window != None:
            self.dialog1.set_transient_for(parent_window)
            self.dialog1.set_modal(True)

    def run(self):
        dia_result = self.dialog1.run()
        if dia_result == RESPONSE_OK:
            self.plugin.debit_account = self.debit_account
            self.plugin.credit_account = self.credit_account
            self.plugin.debit_account_str = self.debit_account_str
            self.plugin.credit_account_str = self.credit_account_str
            try:
                self.plugin.distance_multiplier = \
                    Decimal(self.distance_multiple_entry.get_text())
            except InvalidOperation: pass
        self.dialog1.destroy()
    
    def handle_account_fetch(self, setter):
        account_spec, account_str = self.backend_account_fetch(
            self.dialog1)
        if account_spec != None:
            setter(account_spec, account_str)

    def set_debit_account(self, spec, string):
        self.debit_account = spec
        self.debit_account_str = string
        self.expense_account_label.set_text(string)

    def set_credit_account(self, spec, string):
        self.credit_account = spec
        self.credit_account_str = string
        self.credit_account_label.set_text(string)

    def on_select_expense_account(self, *args):
        self.handle_account_fetch(self.set_debit_account )

    def on_select_credit_account(self, *args):
        self.handle_account_fetch(self.set_credit_account)
