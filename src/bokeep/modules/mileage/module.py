from persistent import Persistent
from bokeep.util import ends_with_commit
from decimal import Decimal

from gui import trustor_entry

from decimal import Decimal
from datetime import datetime
from bokeep.book_transaction import \
    Transaction, FinancialTransaction, FinancialTransactionLine, \
    BoKeepTransactionNotMappableToFinancialTransaction

ZERO = Decimal(0)
NEG_1 = Decimal(-1)

class MileageTransaction(Transaction):
    def __init__(self):
        self.transfer_amount = Decimal(0)

    def get_financial_transactions(self):
        # you should throw BoKeepTransactionNotMappableToFinancialTransaction
        # under some conditions
        return FinancialTransaction(
            (FinancialTransactionLine(self.get_transfer_amount()),
             FinancialTranactionLine(self.get_transfer_amount() * NEG_1) )
            )

    def get_transfer_amount(self):
        return self.transfer_amount

trust_transaction_types = {
    0: MileageTransaction
}

def null_edit_function(*args):
    pass

def trustor_editable_editor(trans, trans_id, module, gui_parent):
    editor = trustor_entry(trans, trans_id, module, gui_parent, True)
    return editor

def trustor_viewonly_editor(trans, trans_id, module, gui_parent):
    editor = trustor_entry(trans, trans_id, module, gui_parent, False)
    return editor

trust_edit_interfaces_hooks = {
    0: trustor_editable_editor,
    }

trust_view_interfaces_hooks = {
    0: trustor_viewonly_editor,
    }

trust_transaction_descriptors = {
    0: "Mileage",
}

class MileageModule(Persistent):
    def register_transaction(self, front_end_id, trust_trans):
        pass

    def remove_transaction(self, front_end_id):
        pass

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
    
