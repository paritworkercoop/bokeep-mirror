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

from decimal import Decimal
from datetime import datetime
from bokeep.book_transaction import \
    Transaction, FinancialTransaction, FinancialTransactionLine, \
    BoKeepTransactionNotMappableToFinancialTransaction
from gui import mileage_entry

ZERO = Decimal(0)
ONE = Decimal(1)
NEG_1 = Decimal(-1)
TWO_PLACES = Decimal('0.01')

class MileageTransaction(Transaction):
    def __init__(self, mileage_plugin):
        Transaction.__init__(self, mileage_plugin)
        self.distance = Decimal(ZERO)
        self.trans_date = datetime.today()

    def make_trans_line(self, account_spec, negate=False):
        amount = (self.get_distance() * \
            self.associated_plugin.distance_multiplier).quantize(TWO_PLACES)
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
        #self.debit_account = self.credit_account = None
        self.debit_account = self.credit_account = ('Assets',)
        self.distance_multiplier = ONE
        self.trans_registry = {}

    def get_debit_account(self):
        return self.debit_account

    def get_credit_account(self):
        return self.credit_account

    def run_configuration_interface(
        self, parent_window, backend_account_fetch):
        pass

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
    
    
