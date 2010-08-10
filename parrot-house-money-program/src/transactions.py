# built-in python imports
from datetime import date
from random import shuffle

# gtk imports
from gtk import ListStore

# python-gnucash imports
from gnucash import GncNumeric, Split
from gnucash import Transaction as gnucash_Transaction

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
        assert( self.debit_account != -1 )
        debit_account = gnucash_thread.member_accounts[ self.debit_account ]
        debit_amount = GncNumeric()
        debit_amount.numerator = self.debit_amount.numerator
        debit_amount.denominator = self.debit_amount.denominator
        debit_split = Split( gnucash_thread.gnucash_session.book,
                             debit_amount, debit_account )
        credit_account = self.get_gnucash_credit_account(gnucash_thread)
        credit_amount = GncNumeric()
        credit_amount.numerator = self.debit_amount.numerator * -1
        credit_amount.denominator = self.debit_amount.denominator
        credit_split = Split( gnucash_thread.gnucash_session.book,
                              credit_amount, credit_account )
        gnucash_trans = gnucash_Transaction(
            gnucash_thread.gnucash_session.book,
            credit_account.commodity,
            (credit_split, debit_split) )

        self.set_transaction_date(gnucash_trans)
        gnucash_trans.description = self.description

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
        split_list = []
        credit_amount = GncNumeric('0')

        paid_by = member_list[self.credit_account][MEMBER_NAME]
        
        for line in self.item_list:
            line_description, line_amount = line[0], line[1]
            line_amount = GncNumeric(line_amount)
            
            # If GST
            gst = line[3+len(member_list)]
            pst = line[3+len(member_list)+1]
            if gst and not pst:
                line_amount = GncNumeric('1.06') * line_amount
            elif pst and not gst:
                line_amount = GncNumeric('1.07') * line_amount
            elif gst and pst:
                line_amount = GncNumeric('1.13') * line_amount
                
            member_subset_list = [i
                                  for i in xrange(len(member_list))
                                  if line[3+i] ]
            shuffle(member_subset_list)
            
            ONE = GncNumeric(1)
            num_members = GncNumeric( len(member_subset_list) ) + ONE
            line_splits = []
            for member in member_subset_list:
                num_members = num_members - ONE
                share_of_item = line_amount / num_members
                split = Split(gnucash_thread.gnucash_session.book,
                              share_of_item,
                              gnucash_thread.member_accounts[member] )
                credit_amount = credit_amount - share_of_item
                line_splits.append( split )
                split.memo = "1/%s %s" % (len(member_subset_list),
                                          line_description)
                line_amount = line_amount - share_of_item
                
            split_list.extend( line_splits )

        split = Split(
            gnucash_thread.gnucash_session.book,
            credit_amount,
            self.get_gnucash_credit_account(gnucash_thread) )
        split.memo = "paid for"
        split_list.append(split)
        

        if len(split_list) > 2:
            trans = gnucash_Transaction(
                gnucash_thread.gnucash_session.book,
                split_list[0].account.commodity,
                split_list )
            self.set_transaction_date(trans)
            trans.description = paid_by + " paid for"
    
# These two lists need to match
transaction_classes = [ LoanTransaction, ExchangeTransaction,
                        ShoppingTransaction ]

transaction_view_classes = [LoanView, ExchangeView, ShoppingView]

for i, transaction_class in enumerate(transaction_classes):
    transaction_class.trans_type_index = i

