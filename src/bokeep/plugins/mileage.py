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

from decimal import Decimal, InvalidOperation
from datetime import datetime, date

from gtk import RESPONSE_OK, Label, Dialog, DIALOG_MODAL, STOCK_OK, \
    STOCK_CANCEL, RESPONSE_CANCEL, Button, Entry, Table, Calendar, HBox

from bokeep.book_transaction import \
    Transaction, FinancialTransaction, FinancialTransactionLine
from bokeep.simple_trans_editor import SimpleTransactionEditor
from bokeep.simple_plugin import SimplePlugin

# One instance for each BoKeep transaction.
# Contains all the data of the BoKeep transaction and provides it to the
# back-end plugin.  Member variables are automatically saved.
class MileageTransaction(Transaction):
    def __init__(self, mileage_plugin):
        # Python doesn't automatically initialise the superclass, so we will.
        super(MileageTransaction,self).__init__(mileage_plugin)
        
        # Defaults for the new BoKeep transaction.
        self.distance = Decimal(0)
        self.trans_date = datetime.today()

    def make_trans_line(self, account_spec, negate=False):
        TWO_PLACES = Decimal('0.01')
        amount = (self.distance * \
            self.associated_plugin.distance_multiplier).quantize(
            TWO_PLACES)
        if negate:
            amount = -amount
        return_value =  FinancialTransactionLine(amount)
        return_value.account_spec = account_spec
        return return_value

    # Used by the back-end plugin to acquire the financial transactions of this
    # BoKeep transaction.
    def get_financial_transactions(self):
        # A financial transaction is composed of several transaction lines
        # that sum to zero (balance).
        ft = FinancialTransaction(
            (self.make_trans_line(self.associated_plugin.debit_account),
             self.make_trans_line(self.associated_plugin.credit_account, True) )
            )
        ft.description = 'Mileage'
        ft.trans_date = self.trans_date
        ft.currency = self.associated_plugin.currency
        
        # Return several financial transactions that together represent this
        # BoKeep transaction.
        return (ft,)

# GUI for editing a BoKeep transaction.
class MileageEditor(SimpleTransactionEditor):
    def simple_init_before_show(self):
        # Setup the calendar.
        calendar = Calendar()
        self.mainvbox.pack_start(calendar)
        calendar.select_month(
            self.trans.trans_date.month-1, self.trans.trans_date.year)
        calendar.select_day(self.trans.trans_date.day)
        calendar.connect('day-selected', self.on_cal_date_changed)
        
        # Setup the distance travelled entry.
        distance_box = HBox()
        distance_label = Label('Distance (km/miles):')
        distance_label.set_alignment(1.0, 0.5) # right, centre
        distance_box.pack_start(distance_label)
        distance_entry = Entry()
        distance_box.pack_end(distance_entry)
        self.mainvbox.pack_end(distance_box)
        distance_entry.set_text(str(self.trans.distance))
        distance_entry.connect('changed', self.on_amount_entry_changed)

    def on_amount_entry_changed(self, widget):
        try:
            self.trans.distance = Decimal(widget.get_text())
        except InvalidOperation:
            pass
        else:
            self.change_register_function()

    def on_cal_date_changed(self, widget):
        (year, month, day) = widget.get_date()
        self.trans.trans_date = date(year, month+1, day)
        self.change_register_function()

# GUI for user to change preferences.
# Preferences are saved to the MileagePlugin.
class MileageConfigDialog(object):
    def __init__(self, parent_window, backend_account_fetch, plugin):
        self.parent_window = parent_window
        self.backend_account_fetch = backend_account_fetch
        self.plugin = plugin
    
    # Display the plugin's configuration and save it to the MileagePlugin if the
    # user clicks OK.
    def run(self):
        self.dia = Dialog('Mileage Configuration',
             self.parent_window, DIALOG_MODAL,
             (STOCK_OK, RESPONSE_OK,
             STOCK_CANCEL, RESPONSE_CANCEL ) )
        
        table = Table(4, 2)
        table.set_row_spacings(4)
        table.set_col_spacings(4)
        
        # Setup the expense account selector.
        self.expense_account_label = Label()
        self.expense_account_label.set_alignment(1.0, 0.5) # right, centre
        table.attach(self.expense_account_label, 0, 1, 0, 1)
        self.expense_account_button = Button('Select Expense Account')
        self.set_debit_account(self.plugin.debit_account,
                               self.plugin.debit_account_str)
        self.expense_account_button.connect('clicked',
                                            self.on_select_expense_account)
        table.attach(self.expense_account_button, 1, 2, 0, 1)
        
        # Setup the credit account selector.
        self.credit_account_label = Label()
        self.credit_account_label.set_alignment(1.0, 0.5) # right, centre
        table.attach(self.credit_account_label, 0, 1, 1, 2)
        self.credit_account_button = Button('Select Credit Account')
        self.set_credit_account(self.plugin.credit_account,
                                self.plugin.credit_account_str)
        self.credit_account_button.connect('clicked',
                                           self.on_select_credit_account)
        table.attach(self.credit_account_button, 1, 2, 1, 2)
        
        # Setup the distance multiple entry.
        distance_multiple_label = Label('Multiply distance by:')
        distance_multiple_label.set_alignment(1.0, 0.5) # right, centre
        table.attach(distance_multiple_label, 0, 1, 2, 3)
        self.distance_multiple_entry = Entry()
        self.distance_multiple_entry.set_text(
                str(self.plugin.distance_multiplier))
        table.attach(self.distance_multiple_entry, 1, 2, 2, 3)
        
        # Setup the currency entry.
        currency_label = Label('Currency:')
        currency_label.set_alignment(1.0, 0.5) # right, centre
        table.attach(currency_label, 0, 1, 3, 4)
        self.currency_entry = Entry()
        self.currency_entry.set_text(self.plugin.currency)
        table.attach(self.currency_entry, 1, 2, 3, 4)
        
        self.dia.vbox.pack_start(table)
        self.dia.vbox.show_all()
        dia_result = self.dia.run()
        
        # If user clicked OK, update settings.
        if dia_result == RESPONSE_OK:
            self.plugin.debit_account = self.debit_account
            self.plugin.credit_account = self.credit_account
            self.plugin.debit_account_str = self.debit_account_str
            self.plugin.credit_account_str = self.credit_account_str
            self.plugin.currency = self.currency_entry.get_text()
            try:
                self.plugin.distance_multiplier = \
                    Decimal(self.distance_multiple_entry.get_text())
            except InvalidOperation:
                pass
        
        self.dia.destroy()

    def handle_account_fetch(self, setter):
        account_spec, account_str = self.backend_account_fetch(self.dia)
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
        self.handle_account_fetch(self.set_debit_account)

    def on_select_credit_account(self, *args):
        self.handle_account_fetch(self.set_credit_account)

# Returns a class that's instantiated once for all entries that this plugin
# provides.
def get_plugin_class():
    return MileagePlugin

# Ties this plugin together and stores the configuration.
# One instance is instantiated upon first use of this plugin.
# After that, this class is reloaded.
class MileagePlugin(SimplePlugin):
    # This plugin provides a single type of BoKeep entry for logging mileage.
    # However, another plugin may provide several types of BoKeep entries.
    ALL_TRANSACTION_TYPES = (MileageTransaction,)
    DEFAULT_TYPE_STRS = ('Mileage Plugin',)
    EDIT_INTERFACES = (MileageEditor,)
    
    # Class variables are used to store the configuration.
    debit_account = ('Expenses',)
    credit_account = ('Assets',)
    debit_account_str = 'Expenses'
    credit_account_str = 'Assets'
    currency = 'CAD'
    distance_multiplier = Decimal(1)
    
    def run_configuration_interface(self, parent_window, backend_account_fetch):
        dialog = MileageConfigDialog(parent_window, backend_account_fetch, self)
        dialog.run()