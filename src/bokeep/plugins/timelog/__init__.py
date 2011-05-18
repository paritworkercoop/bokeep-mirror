# Copyright (C) 2011  ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
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
from datetime import date
from decimal import Decimal

# zodb imports
from persistent.list import PersistentList

# gtk imports
from gtk import \
    Label, Dialog, STOCK_OK, RESPONSE_OK, HBox, ComboBox, ListStore, \
    combo_box_new_text
from gobject import TYPE_PYOBJECT

# bokeep imports
from bokeep.simple_trans_editor import SimpleTransactionEditor
from bokeep.simple_plugin import SimplePlugin
from bokeep.book_transaction import \
    Transaction, BoKeepTransactionNotMappableToFinancialTransaction
from bokeep.gtkutil import \
    create_editable_type_defined_listview_and_model, COMBO_NO_SELECTION

def create_timelog_new_row(timelog_plugin):
    def timelog_new_row():
        return ('new employee', date.today(), Decimal(0), 'task')
    return timelog_new_row

class MultiEmployeeTimelogEditor(SimpleTransactionEditor):
    def simple_init_before_show(self):
        self.model, self.tv, tree_box = create_editable_type_defined_listview_and_model(
            ( ('Employee', str), ('Day', date), ('Hours', Decimal), ('Description', str), ),
            create_timelog_new_row(self.plugin),
            self.trans.timelog_list, self.change_register_function,
            )
        self.mainvbox.pack_start( tree_box, expand=False)

class MultiEmployeeTimelogEntry(Transaction):
    def __init__(self, associated_plugin):
        Transaction.__init__(self, associated_plugin)
        self.timelog_list = PersistentList()

    def get_financial_transactions(self):
        raise BoKeepTransactionNotMappableToFinancialTransaction(
            """Timelog plugin doesn't put anything directly in backend yet, but """
            """will be picked up by payroll plugin""")

PAYROLL_PLUGIN = "bokeep.plugins.payroll"

PAYROLL_PLUGIN_STR_POSITION, PAYROLL_PLUGIN_STORE_POSITION = range(2)

class TimelogPlugin(SimplePlugin):
    ALL_TRANSACTION_TYPES = (MultiEmployeeTimelogEntry,)
    DEFAULT_TYPE_STRS =("Multi employee timelog entry",)
    EDIT_INTERFACES = (MultiEmployeeTimelogEditor,)

    def __init__(self):
        SimplePlugin.__init__(self)
        self.payroll_plugin = None

    def payroll_plugin_selection_combobox_changed(self, combobox, model):
        if combobox.get_active() == COMBO_NO_SELECTION:
            self.payroll_plugin = None
        else:
            self.payroll_plugin = \
                model[combobox.get_active()][PAYROLL_PLUGIN_STORE_POSITION]

    def run_configuration_interface(
        self, parent_window, backend_account_fetch, book=None):
        # shell will set this keyword argument, to be replaced with
        # a normal argument
        assert( book != None )
        dia = Dialog(
            "Timelog plugin configuration", parent_window,
            buttons=(STOCK_OK, RESPONSE_OK))
        hbox = HBox()
        dia.vbox.pack_start( hbox, expand=False )
        
        if book.has_module_enabled("bokeep.plugins.payroll"):
            hbox.pack_start( Label("Pick a payroll plugin instance"),
                             expand=False )
            payroll_combo = combo_box_new_text()
            payroll_liststore = ListStore(str, TYPE_PYOBJECT)
            payroll_liststore.append( (PAYROLL_PLUGIN,
                                       book.get_module(PAYROLL_PLUGIN)) )
            payroll_combo.set_model(payroll_liststore)
            changed_handler_id = payroll_combo.connect(
                "changed",
                self.payroll_plugin_selection_combobox_changed,
                payroll_liststore)
            # don't allow the above event handler to be called we set set
            # the active selection in the combo programatically
            payroll_combo.handler_block(changed_handler_id)
            if not hasattr(self, 'payroll_plugin') or \
                    self.payroll_plugin == None:
                payroll_combo.set_active(COMBO_NO_SELECTION)
            else:
                # once we have support for multiple plugin instances we'll need
                # to change this
                payroll_combo.set_active(0)
            # don't allow the above event handler to be called while we set
            # the active selection in the combo programatically
            payroll_combo.handler_unblock(changed_handler_id)

            hbox.pack_start(payroll_combo, expand=True)
        else:
            hbox.pack_start(Label("no payroll plugin instance available"))
        dia.show_all()
        dia.run()
        dia.destroy()
        
def get_plugin_class():
    return TimelogPlugin
