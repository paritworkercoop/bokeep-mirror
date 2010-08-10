from members import member_list, ACCOUNT_PATH
from gnucash import Session, Transaction, Split

class GnuCashThread(object):
    def __init__(self, gnucash_file):
        self.gnucash_session = Session('file:%s' % gnucash_file )
        self.member_accounts = [
            self.gnucash_session.book.account_group.account_from_path(
            member[ACCOUNT_PATH] )
            for member in member_list ]
    
    def join_init_thread(self):
        pass

    def end(self):
        self.gnucash_session.save()
        self.gnucash_session.end()
    
