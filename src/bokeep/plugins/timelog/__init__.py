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
from gtk import Label, Dialog, STOCK_OK, RESPONSE_OK, HBox, ComboBox

# bokeep imports
from bokeep.simple_trans_editor import SimpleTransactionEditor
from bokeep.simple_plugin import SimplePlugin
from bokeep.book_transaction import \
    Transaction, BoKeepTransactionNotMappableToFinancialTransaction
from bokeep.gtkutil import \
    create_editable_type_defined_listview_and_model 

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

class TimelogPlugin(SimplePlugin):
    ALL_TRANSACTION_TYPES = (MultiEmployeeTimelogEntry,)
    DEFAULT_TYPE_STRS =("Multi employee timelog entry",)
    EDIT_INTERFACES = (MultiEmployeeTimelogEditor,)

    def run_configuration_interface(
        self, parent_window, backend_account_fetch, book=None):
        # shell will set this keyword argument, to be replaced with
        # a normal argument
        assert( book != None )
        dia = Dialog(
            "Timelog plugin configuration", parent_window,
            buttons=(STOCK_OK, RESPONSE_OK))
        hbox = HBox()
        dia.get_content_area().pack_start( hbox, expand=False )
        
        if book.has_module_enabled("bokeep.plugins.payroll"):
            hbox.pack_start( Label("Pick a payroll plugin instance"),
                             expand=False )
            payroll_combo = ComboBox()
            hbox.pack_start(payroll_combo, expand=True)
        else:
            hbox.pack_start(Label("no payroll plugin instance available"))
        dia.show_all()
        dia.run()
        dia.destroy()
        
def get_plugin_class():
    return TimelogPlugin
