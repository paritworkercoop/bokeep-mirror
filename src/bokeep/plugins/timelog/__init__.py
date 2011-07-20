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
from itertools import chain

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
from bokeep.util import get_and_establish_attribute
from bokeep.objectregistry import ObjectRegistry

def create_timelog_new_row(timelog_plugin):
    def timelog_new_row():
        return (None, date.today(), Decimal(0), 'task')
    return timelog_new_row

EMPLOYEE, DAY, HOURS, DESCRIPTION = range(4)

class MultiEmployeeTimelogEditor(SimpleTransactionEditor):
    def simple_init_before_show(self):
        if getattr(self.plugin, 'payroll_plugin', None) == None:
            self.mainvbox.pack_start(
                Label("no payroll plugin for timelog plugin to work with "
                      "selected. Go to your book and plugin configuration "
                      "dialogs") )
        else:
            # its good that we're using sorted here not only for sorting by
            # the keys in the employee dictionary index, but also because we
            # only iterate through the list of employees provided by the
            # payroll plugin once, we wouldn't want to call
            # get_employees() twice and get two different dicts
            sorted_employee_list = sorted(
                self.plugin.payroll_plugin.get_employees().iteritems() )
            employee_listing = tuple(
                chain( (None, ),
                       (value for key, value in sorted_employee_list)
                       ) ) # end chain, end tuple

            employee_combo_specifier = tuple( chain(
                    (False, employee_listing,'None'),
                    (key for key, value in sorted_employee_list),
                ) ) # end chain, end tuple

            # providing a null function for change registration because
            # we're going to be installing our own event handlers to
            # react to the model changes and index them by date
            # its bad to allow persistence to happen before then because
            # we want the changes to self.trans.timelog_list and
            # our index of it by date to happen automically
            self.model, self.tv, tree_box = \
                create_editable_type_defined_listview_and_model(
                ( ('Employee',
                   employee_combo_specifier, 
                   ), # employee type tuple
                  ('Day', date), ('Hours', Decimal), ('Description', str), ),
                create_timelog_new_row(self.plugin),
                self.trans.timelog_list, self.change_register_function,
                insert_pre_hook=self.timelog_inserted_handler,
                change_pre_hook=self.trans.remove_timelog_entry_from_registry,
                change_post_hook=self.timelog_after_row_changed_handler,
                del_pre_hook=self.trans.remove_timelog_entry_from_registry,
                )

            self.mainvbox.pack_start( tree_box, expand=False)

    def timelog_inserted_handler(self, index, timelog_entry):
        registry = self.plugin.get_timelog_entry_registry()
        registry.register_interest_by_non_unique_key(
            date.min, timelog_entry, self.trans)
        
    def timelog_after_row_changed_handler(self,  index, timelog_entry, new_row):
        registry = self.plugin.get_timelog_entry_registry()
        # don't even bother playing with the registry until the date is set
        # to something real instead of date.min [ date(1,1,1) ]
        # now we re-register with the new date
        registry.register_interest_by_non_unique_key(
            date.min if timelog_entry[DAY]==None else timelog_entry[DAY],
            timelog_entry, self.trans )

class MultiEmployeeTimelogEntry(Transaction):
    def __init__(self, associated_plugin):
        Transaction.__init__(self, associated_plugin)
        self.timelog_list = PersistentList()

    def remove_timelog_entry_from_registry(self, index, timelog_entry,
                                           new_row=None):
        registry = self.associated_plugin.get_timelog_entry_registry()
        object_keys = tuple(registry.get_keys_for_object(timelog_entry))

        # we're only tracking by one key, by date
        assert( len(object_keys) == 1)
        # BIG assumption, that we're the only one with an interest in the
        # object being tracked; to enforce this we're going to have to
        # lock up this whole interface when the timelog entries are
        # non-new
        return registry.final_deregister_interest_for_obj_non_unique_key(
            object_keys[0], timelog_entry, self )

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

    def remove_transaction(self, front_end_id):
        trans = self.trans_registry[front_end_id]
        registry = self.get_timelog_entry_registry()
        # The big assumption here is that success in removing all
        # individual timelog entries, and that requires they not be
        # registered by anything else. This isn't good, it means
        # the delete feature in the shell should actually check with us
        # e.g. we need an api change
        #
        # in the meantime, we should at least limit shell level
        # delete to new transactions unless a special mode is  enabled
        result = all(
            trans.remove_timelog_entry_from_registry(i, entry)
            for i, entry in enumerate(trans.timelog_list)
            )
        assert(result)
        if result:
            SimplePlugin.remove_transaction(self, front_end_id)

    def get_timelog_entry_registry(self):
        return get_and_establish_attribute(
            self, 'timelog_registry', ObjectRegistry )

    def payroll_plugin_selection_combobox_changed(self, combobox, model):
        if combobox.get_active() == COMBO_NO_SELECTION:
            self.payroll_plugin = None
        else:
            self.payroll_plugin = \
                model[combobox.get_active()][PAYROLL_PLUGIN_STORE_POSITION]

    def run_configuration_interface(
        self, parent_window, backend_account_fetch, book):
        # shell will set this keyword argument, to be replaced with
        # a normal argument
        assert( book != None )
        dia = Dialog(
            "Timelog plugin configuration", parent_window,
            buttons=(STOCK_OK, RESPONSE_OK))
        hbox = HBox()
        dia.vbox.pack_start( hbox, expand=False )
        
        if book.has_enabled_frontend_plugin("bokeep.plugins.payroll"):
            hbox.pack_start( Label("Pick a payroll plugin instance"),
                             expand=False )
            payroll_combo = combo_box_new_text()
            payroll_liststore = ListStore(str, TYPE_PYOBJECT)
            payroll_liststore.append( (PAYROLL_PLUGIN,
                                       book.get_frontend_plugin(PAYROLL_PLUGIN)) )
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
