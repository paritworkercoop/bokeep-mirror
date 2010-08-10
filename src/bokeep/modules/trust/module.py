from persistent import Persistent
from bokeep.util import ends_with_commit
from decimal import Decimal

from core import TrustMoneyInTransaction, TrustMoneyOutTransaction

TRUST_MONEY_IN, TRUST_MONEY_OUT = range(2)

trust_transaction_types = {
    TRUST_MONEY_IN: TrustMoneyInTransaction,
    TRUST_MONEY_OUT: TrustMoneyOutTransaction
}

def null_edit_function(*args):
    pass

trust_edit_interfaces_hooks = {
    TRUST_MONEY_IN: null_function,
    TRUST_MONEY_OUT: null_function,
    }

trust_view_interfaces_hooks = {
    TRUST_MONEY_IN: null_function,
    TRUST_MONEY_OUT: null_function,
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

    def init_trustors_database(self):
        self.trustors_database = {}        

    def init_transaction_tracker(self):
        self.transaction_track_database = {}

    def init_trust_database(self):
        self.init_trustors_database()
        self.init_transaction_tracker()
        
    def ensure_trust_database(self):
        if not hasattr(self, 'trustors_database'):
            self.init_trustors_database()
        if not hasattr(self, 'transaction_track_database'):
            self.init_transaction_tracker()

    def has_trustor(self, trustor):
        self.ensure_trust_database()
        return trustor in self.trustors_database

    @ends_with_commit
    def drop_trustor_by_name(self, trustor_name):
        if not(self.has_trustor(trustor_name)):
            raise Exception("there is no trustor named %s")
        
        trustor = self.get_trustor(trustor_name)

        if len(trustor.transactions) > 0:
            raise Exception("Cannot delete trustor named %s, there are associated transactions" % trustor_name)
        
        del self.trustors_database[trustor_name]
        self._p_changed = True

    @ends_with_commit
    def add_trustor_by_name(self, trustor_name):
        self.ensure_trust_database()
        if self.has_trustor(trustor_name):
            raise Exception("there already is a trustor named %s" % trustor_name)
        self.trustors_database[trustor_name] = Trustor(name=trustor_name)
        self._p_changed = True


    def get_trustor(self, trustor_name):
        self.ensure_trust_database()
        return self.trustors_database[trustor_name]

    @ends_with_commit
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
        if not trustor in self.trustors_database:
            raise Exception("there is no trustor %s, you should check with "
                            "has_trustor() or find the trustor via "
                            "get_trustors() " % trustor_name)
        trustor = self.get_trustor(trustor_name)
        trustor.add_transaction(trust_trans)
        self.transaction_track_database[front_end_id] = (trust_trans,
                                                         trustor_name)
        trust_trans.set_trustor(trustor)

    def disassociate_trustor_with_transaction(self, front_end_id,
                                             trust_trans, trustor_name):
        self.ensure_trust_database()
        trustor = self.get_trustor(trustor_name)
        trustor.del_transaction(trust_trans)
        self.transaction_track_database[front_end_id] = (trust_trans, None)
        trust_trans.set_trustor(None)

    def register_transaction(self, front_end_id, trust_trans):
        self.ensure_trust_database()
        self.transaction_track_database[front_end_id] = (trust_trans, None)
        self._p_changed = True

    def remove_transaction(self, front_end_id):
        self.ensure_trust_database()
        trust_trans, trustor_name = \
            self.transaction_track_database[front_end_id]
        if trustor_name != None:
            self.diassociate_trustor_with_transaction(
                front_end_id, trust_trans, trustor_name)
        del self.transaction_track_database[front_end_id]

    def get_trustors(self):
        self.ensure_trust_database()
        return self.trustors_database

    @staticmethod
    def get_transaction_type_codes():
        return trust_transaction_types.keys()

    @staticmethod
    def get_transaction_type_from_code(code):
        return trust_transaction_types[code]

    @staticmethod
    def get_transaction_type_pulldown_string_from_code(code):
        return trust_transaction_descriptors[code]
        
    @staticmethod
    def get_transaction_edit_interface_hook_from_code(code):
        return trust_edit_interfaces_hooks[code]

    @staticmethod
    def get_transaction_view_interface_hook_fom_code(code):
        return trust_view_interfaces_hooks[code]

    
