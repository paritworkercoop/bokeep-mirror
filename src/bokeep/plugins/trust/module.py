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
# Author: Jamie Campbell <jamie@parit.ca>
# Author: Mark Jenkins <mark@parit.ca>

from persistent import Persistent
from decimal import Decimal

from GUIs.entry.trustor_entry import trustor_entry
from GUIs.management.trustor_management import trustor_management

from core import TrustMoneyInTransaction, TrustMoneyOutTransaction

TRUST_MONEY_IN, TRUST_MONEY_OUT = range(2)

trust_transaction_types = {
    TRUST_MONEY_IN: TrustMoneyInTransaction,
    TRUST_MONEY_OUT: TrustMoneyOutTransaction
}

def null_edit_function(*args):
    pass

def trustor_editable_editor(trans, trans_id, module, gui_parent,
                            change_register_function):
    print 'generating an editor for trustors'
    editor = trustor_entry(trans, trans_id, module, gui_parent, True,
                           change_register_function)
    return editor

def trustor_viewonly_editor(trans, trans_id, module, gui_parent,
                            change_register_function):
    editor = trustor_entry(trans, trans_id, module, gui_parent, False,
                           change_register_function)
    return editor

trust_edit_interfaces_hooks = {
    TRUST_MONEY_IN: trustor_editable_editor,
    TRUST_MONEY_OUT: trustor_editable_editor,
    }

trust_view_interfaces_hooks = {
    TRUST_MONEY_IN: trustor_viewonly_editor,
    TRUST_MONEY_OUT: trustor_viewonly_editor,
    }

trust_transaction_descriptors = {
    TRUST_MONEY_IN: "Trust Money In",
    TRUST_MONEY_OUT: "Trust Money Out",
}

class Trustor(Persistent):
    def __init__(self, name=None):
        self.name = name
        self.transactions = []
    
    def add_transaction(self, trust_trans):
        self.transactions.append(trust_trans)
        self._p_changed = True

    def del_transaction(self, trust_trans):
        self.transactions.remove(trust_trans)
        self._p_changed = True

    def has_transaction(self, trust_trans):
        for transaction in self.transactions:
            if transaction == trust_trans:
                return True
        return False

    def clear_transactions(self):
        while len(self.transactions) > 0:
            self.del_transaction(self.transactions[0])

    def get_balance(self):
        curr_balance = Decimal('0')
        for transaction in self.transactions:
            curr_balance += transaction.get_transfer_amount()

        return curr_balance

class TrustModule(Persistent):
    def __init__(self):
        self.init_trust_database()

    def run_configuration_interface(self, parent_window,
                                    backend_account_fetch=None):
        trustor_management(self, parent_window, backend_account_fetch)

    def init_trustors_database(self):
        self.trustors_database = {}        

    def init_transaction_tracker(self):
        self.transaction_track_database = {}

    def init_currency(self):
        self.currency = "CAD"

    def init_trust_database(self):
        self.init_currency()
        self.init_trustors_database()
        self.init_transaction_tracker()
        
    def ensure_trust_database(self):
        if not hasattr(self, 'trustors_database'):
            self.init_trustors_database()
        if not hasattr(self, 'transaction_track_database'):
            self.init_transaction_tracker()
        if not hasattr(self, "currency"):
            self.init_currency()

    def get_currency(self):
        self.ensure_trust_database()
        return self.currency

    def has_trustor(self, trustor):
        self.ensure_trust_database()
        return trustor in self.trustors_database

    def drop_trustor_by_name(self, trustor_name):
        if not(self.has_trustor(trustor_name)):
            raise Exception("there is no trustor named %s")
        
        trustor = self.get_trustor(trustor_name)

        if len(trustor.transactions) > 0:
            raise Exception("Cannot delete trustor named %s, there are associated transactions" % trustor_name)
        
        del self.trustors_database[trustor_name]
        self._p_changed = True

    def add_trustor_by_name(self, trustor_name):
        self.ensure_trust_database()
        if self.has_trustor(trustor_name):
            raise Exception("there already is a trustor named %s" % trustor_name)
        self.trustors_database[trustor_name] = Trustor(name=trustor_name)
        self._p_changed = True


    def get_trustor(self, trustor_name):
        self.ensure_trust_database()
        if self.has_trustor(trustor_name):
            return self.trustors_database[trustor_name]
        else:
            return None

    def rename_trustor(self, old_name, new_name):
        if not(self.has_trustor(old_name)):
            raise Exception("there is no trustor named %s" % old_name)

        if self.has_trustor(new_name):
            raise Exception("there is already a trustor named %s" % new_name)

        trustor = self.get_trustor(old_name)
        trustor.name = new_name
        del self.trustors_database[old_name]
        self.trustors_database[new_name] = trustor
        self._p_changed = True

    def associate_transaction_with_trustor(self, front_end_id,
                                           trust_trans, trustor_name):
        self.ensure_trust_database()
        if not trustor_name in self.trustors_database:
            raise Exception("there is no trustor %s, you should check with "
                            "has_trustor() or find the trustor via "
                            "get_trustors() " % trustor_name)


        trustor = self.get_trustor(trustor_name)

        #if the transaction was already associated with another trustor, 
        #dissociate it
        if not trust_trans.get_trustor() == None and not trust_trans.get_trustor() == trustor:
            self.disassociate_trustor_with_transaction(front_end_id, trust_trans, trust_trans.get_trustor().name)

        trust_trans.set_trustor(trustor)

        #don't re-add...
        if not trustor.has_transaction(trust_trans):
            trustor.add_transaction(trust_trans)

        self.transaction_track_database[front_end_id] = (trust_trans,
                                                         trustor_name)
        self._p_changed = True

    def disassociate_trustor_with_transaction(self, front_end_id,
                                             trust_trans, trustor_name):
        self.ensure_trust_database()
        trustor = self.get_trustor(trustor_name)
        trustor.del_transaction(trust_trans)
        self.transaction_track_database[front_end_id] = (trust_trans, None)
        trust_trans.set_trustor(None)
        self._p_changed = True

    def register_transaction(self, front_end_id, trust_trans):
        self.ensure_trust_database()
        self.transaction_track_database[front_end_id] = (trust_trans, None)
        self._p_changed = True

    def remove_transaction(self, front_end_id):
        self.ensure_trust_database()
        trust_trans, trustor_name = \
            self.transaction_track_database[front_end_id]
        if trustor_name != None:
            self.disassociate_trustor_with_transaction(
                front_end_id, trust_trans, trustor_name)
        del self.transaction_track_database[front_end_id]

    def has_transaction(self, front_end_id):
        return front_end_id in self.transaction_track_database

    def get_trustors(self):
        self.ensure_trust_database()
        return self.trustors_database

    def set_cash_account(self, account_spec_obj, cash_acct_str='cash'):
        self.cash_account = account_spec_obj
        self.cash_account_str = cash_acct_str

    def set_trust_liability_account(self, account_spec_obj,
                                    liability_account_str='liability'):
        self.trust_liability_account = account_spec_obj
        self.trust_liability_account_str = liability_account_str

    @staticmethod
    def get_transaction_type_codes():
        return trust_transaction_types.keys()

    @staticmethod
    def get_transaction_type_from_code(code):
        return trust_transaction_types[code]

    @staticmethod
    def get_transaction_code_from_type(ty):
        for entry in trust_transaction_types:
            if trust_transaction_types[entry] == ty:
                return entry

        return None

    @staticmethod
    def get_transaction_type_pulldown_string_from_code(code):
        return trust_transaction_descriptors[code]
        
    @staticmethod
    def get_transaction_edit_interface_hook_from_code(code):
        return trust_edit_interfaces_hooks[code]

    @staticmethod
    def get_transaction_view_interface_hook_from_code(code):
        return trust_view_interfaces_hooks[code]

    @staticmethod
    def get_transaction_edit_interface_hook_from_type(ty):
        code = TrustModule.get_transaction_code_from_type(ty)

        if not code == None:
            return trust_edit_interfaces_hooks[code]
        else:
            return None

    @staticmethod
    def get_transaction_view_interface_hook_from_type(ty):
        code = TrustModule.get_transaction_code_from_type(ty)

        if not code == None:
            return trust_view_interfaces_hooks[code]
        else:
            return None
    
