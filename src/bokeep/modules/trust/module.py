from persistent import Persistent
from bokeep.util import ends_with_commit

class Trustor(Persistent):
    def __init__(self, name=None):
        self.name = None
        self.transactions = []
    
    def add_transaction(self, trust_trans):
        self.transactions.append(trust_trans)
        self._p_changed = True

    def del_transaction(self, trust_trans):
        self.transactions.remove(trust_trans)
        self._p_changed = True

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
    def add_trustor_by_name(self, trustor_name):
        self.ensure_trust_database()
        if self.has_trustor(trustor_name):
            raise Exception("there already is a trustor named %s")
        self.trustors_database[trustor_name] = Trustor(name=trustor_name)
        self._p_changed = True


    def get_trustor(self, trustor_name):
        self.ensure_trust_database()
        return self.trustors_database[trustor_name]

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
        return self.trustors_database.iterkeys()
            
    
