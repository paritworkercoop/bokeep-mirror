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
from decimal import Decimal

# zodb imports
from persistent import Persistent
from persistent.mapping import PersistentMapping

# bokeep imports
from bokeep.book_transaction import \
    Transaction, FinancialTransaction, FinancialTransactionLine, \
    BoKeepTransactionNotMappableToFinancialTransaction
from bokeep.gtkutil import file_selection_path
from bokeep.util import get_module_for_file_path

def get_plugin_class():
    return MultiPageGladePlugin

MULTIPAGEGLADE_CODE = 0

class MultiPageGladePlugin(Persistent):
    def __init__(self):
        self.trans_registry = PersistentMapping()
        self.config_file = None
        self.type_string = "Multi page glade"

    def get_configuration(self):
        if hasattr(self, _v_configuration):
            return self._v_configuration
        else:
            return_value = \
                None if self.config_file == None \
                else get_module_for_file_path(self.config_file)
            if return_value != None:
                self._v_configuration = return_value
            return return_value

    def run_configuration_interface(
        self, parent_window, backend_account_fetch):
        self.config_file = file_selection_path("select config file")

    def register_transaction(self, front_end_id, trust_trans):
        assert( not self.has_transaction(front_end_id) )
        self.trans_registry[front_end_id] = trust_trans

    def remove_transaction(self, front_end_id):
        del self.trans_registry[front_end_id]

    def has_transaction(self, trans_id):
        return trans_id in self.trans_registry

    @staticmethod
    def get_transaction_type_codes():
        return (MULTIPAGEGLADE_CODE,)

    @staticmethod
    def get_transaction_type_from_code(code):
        assert(code == MULTIPAGEGLADE_CODE)
        return MultipageGladeTransaction

    def get_transaction_type_pulldown_string_from_code(self, code):
        assert(code == MULTIPAGEGLADE_CODE)
        return self.type_string
        
    @staticmethod
    def get_transaction_edit_interface_hook_from_code(code):
        return multipage_glade_editor

class MultipageGladeTransaction(Transaction):
    def get_financial_transactions(self):
        # you should throw BoKeepTransactionNotMappableToFinancialTransaction
        # under some conditions
        raise BoKeepTransactionNotMappableToFinancialTransaction(
            "not written yet")

class multipage_glade_editor(object):
    def __init__(self,
                 trans, transid, plugin, gui_parent, change_register_function):
        self.trans = trans
        self.transid = transid
        self.plugin = plugin
        self.gui_parent = gui_parent
        self.change_register_function = change_register_function

    def detach(self):
        pass

def make_sum_entry_val_func(positive_funcs, negative_funcs):
    def return_func(window_list):
        return sum( chain( (positive_function(window_list)
                            for positive_function in positive_funcs),
                           (-negative_function(window_list)
                             for negative_function in negative_funcs) ),
                    Decimal(0) )
    return return_func

def make_get_entry_val(page, entry_name):
    def return_func(window_dict):
        if page not in window_dict:
            raise BoKeepTransactionNotMappableToFinancialTransaction(
                "page %s could not be found" % page)
        if entry_name not in window_dict[page]:
            raise BoKeepTransactionNotMappableToFinancialTransaction(
                "entry %s from page %s not found" % (entry_name, page) )
        try:
            return Decimal( window_dict[page][entry_name].get_text() )
        except ValueError:
            raise BoKeepTransactionNotMappableToFinancialTransaction(
                "entry %s from page %s not convertable to decimal with value "
                "%s" % (entry_name, page,
                        window_dict[page][entry_name].get_text() ) )
    return return_func
