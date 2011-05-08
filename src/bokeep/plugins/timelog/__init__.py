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

# zodb imports
from persistent.list import PersistentList

# gtk imports
from gtk import Label

# bokeep imports
from bokeep.simple_trans_editor import SimpleTransactionEditor
from bokeep.simple_plugin import SimplePlugin
from bokeep.book_transaction import \
    Transaction, BoKeepTransactionNotMappableToFinancialTransaction
from bokeep.gtkutil import \
    create_editable_type_defined_listview_and_model, cell_renderer_date_to_string

def create_timelog_new_row(timelog_plugin):
    def timelog_new_row():
        return ('new employee', cell_renderer_date_to_string(date.today()), '0', 'task')
    return timelog_new_row

class MultiEmployeeTimelogEditor(SimpleTransactionEditor):
    def simple_init_before_show(self):
        self.model, self.tv, tree_box = create_editable_type_defined_listview_and_model(
            ( ('Employee', str), ('Day', date), ('Hours', str), ('Description', str), ),
            ('', '', '', ''),
            create_timelog_new_row(self.plugin),
            self.trans.timelog_list, self.change_register_function,
            )
        self.mainvbox.pack_start( tree_box, expand=False)
        # before populating the liststore, you might want to read this
        # pygtk FAQ:
        # 
        # 13.43. Are there tips for improving performance when adding many
        # rows to a Treeview?

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

def get_plugin_class():
    return TimelogPlugin
