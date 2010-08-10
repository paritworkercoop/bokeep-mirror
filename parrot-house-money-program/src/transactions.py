# built-in python imports
from datetime import date
from random import shuffle

# gtk imports
from gtk import ListStore

# python-gnucash imports
#from gnucash import GncNumeric, Split
#from gnucash import Transaction as gnucash_Transaction

# this project imports
from loan_view import LoanView
from exchange_view import ExchangeView
from shopping_view import ShoppingView
from util import IntDecimalNumber
from members import member_list, MEMBER_NAME

class Transaction(object):
    def __init__(self):
        self.date = date.today()
        self.old = False
        self.modified = True
        self.credit_account = -1

    def convert_to_pickable_form(self):
        pass
    
    def save_in_gnucash(self, gnucash_thread):
        pass

    def get_gnucash_credit_account(self, gnucash_thread):
        assert( self.credit_account != -1 )
        return gnucash_thread.member_accounts[self.credit_account]

    def set_transaction_date(self, gnucash_trans):
        gnucash_trans.date_posted = self.date

class ExchangeTransaction(Transaction):
    def __init__(self):
        Transaction.__init__(self)
        self.debit_amount = IntDecimalNumber()
        self.debit_account = -1
        self.description = "money exchange"

    def save_in_gnucash(self, gnucash_thread):
        pass

class LoanTransaction(ExchangeTransaction):
    def __init__(self):
        ExchangeTransaction.__init__(self)
        self.description = "loan"

class ShoppingTransaction(Transaction):
    def __init__(self):
        Transaction.__init__(self)
        
        # build arguments for the ListStore constructor
        list_store_args = [str, str]

        # a bool for the error NAN error icon, one for each member of the
        # house and two more for the GST and PST columns
        list_store_args.extend( [bool] * (1+len(member_list)+2) )
        
        self.item_list = ListStore(*list_store_args)

    def convert_to_pickable_form(self):
        self.item_list = [ list(item) for item in self.item_list ]

    def save_in_gnucash(self, gnucash_thread):
        pass
    
# These two lists need to match
transaction_classes = [ LoanTransaction, ExchangeTransaction,
                        ShoppingTransaction ]

transaction_view_classes = [LoanView, ExchangeView, ShoppingView]

for i, transaction_class in enumerate(transaction_classes):
    transaction_class.trans_type_index = i

