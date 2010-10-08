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
import transaction
from threading import Thread, Condition
from util import \
    ChangeMessageRecievingThread, EntityChangeManager, entitymod

class FinancialTransactionLine(object):
    """Represents a line in a balanced financial transaction.
    Each line has an amount. Positive numbers are debits, negative numbers
    are credits. The amount must be of the builtin type decimal.Decimal
    
    In addition to amount, some accounting backends allow for other
    attributes to be associated with a financial tranaction line. If you set
    them on instances of this class, they will be picked up and used by
    backend modules that support them.
    Backends that don't support particular attributes will ignore them
    
    account_spec -- specifies an account to associate with the line;
                    will be supported by GnuCash and SerialFile backend modules
                    The format/type of this attribute is backend module
                    specific, eventually, anything using this attribute should
                    be able to get an object of right tu[e simply by
                    communicating with the backend
                    module. (the backend module should also facilitate the
                    selection)
    line_memo -- specifies a string to associate with the line,
                 will be supported by GnuCash and SerialFile backend modules
    """
    def __init__(self, amount):
        self.amount = amount

class FinancialTransaction(object):
    """Represents a balanced financial transaction, which consists of
    FinancialTransactionLine s. The amount of all the FinancialTransactionLine
    s must add up to zero (this is what makes them balanced)

    Extended attributes: (not required, but may be optionally specified,
    will be supported by some backends)
    
    trans_date -- specifies the date of the financial transaction, the
    date should be the one used to include or exclude the transaction from
    income statements and balance sheets. Must be a datetime.date or
    datetime.datetime object. Will be GnuCash and SerialFile backend
    modules

    description -- a description (string) for the entire transaction.
    If the accounting backend supports it, this should be the text used for
    the name on a cheque. Will be supported by GnuCash and SerialFile backend
    modules

    chequenum -- a number (integer) to assign if the transaction is a cheque,
    or other numberic transaction identifier. Will be supported by GnuCash
    and SerialFile backends.
    """
    def __init__(self, lines):
        self.lines = lines

def make_fin_line(amount, accounts, comment):
    line = FinancialTransactionLine(amount)
    line.account_spec = accounts
    line.line_memo = comment
    return line

class BoKeepTransactionNotMappableToFinancialTransaction(Exception):
    pass

class Transaction(Persistent):
    def __init__(self):
        pass

    def get_financial_transactions(self):
        """Return a generator that will provide FinancialTransaction instances
        associated with this bo-keep Transaction to be stored by a
        BackendModule
        """
        raise BoKeepTransactionNotMappableToFinancialTransaction()

class TransactionDeltaManager(EntityChangeManager):
    def __init__(self, running_thread, entity_identifier):
        EntityChangeManager.__init__(self, running_thread, entity_identifier)
        self.change_list = []
        self.attribute_change_index = {}
        # important value, if there have been no function calls this ensures
        # attribute changes are considerd to occure "after" this
        self.latest_function_call = -1 

def new_transaction_committing_thread(book_set):
    commit_thread = TransactionComittingThread(book_set)
    commit_thread.start()
    return commit_thread

class TransactionComittingThread(ChangeMessageRecievingThread):
    def __init__(self, book_set):
        ChangeMessageRecievingThread.__init__(self)
        self.book_set = book_set

    def get_arguments_for_exec_procedure(self):
        # not sure what was going on here, but keep in mind
        # there is now a sub-database for books
        return ((self.dbroot,), {})

    def new_entity_change_manager(self, entity_identifier):
        return TransactionDeltaManager(self, entity_identifier)

    @entitymod
    def mod_transaction_attr(self, delta, attr_name, attr_value):
        # if the attribute has already been changed, and that change was
        # after the last function call, simply replace the attribute change
        if attr_name in delta.attribute_change_index and \
                delta.attribute_change_index[attr_name] > \
                delta.latest_function_call:
            change_position = delta.attribute_change_index[attr_name]
        # else we create a new attribute change
        else:
            delta.attribute_change_index[attr_name] = change_position = \
                len(delta.change_list)
            delta.change_list.append(None)

        # apply the attribute change, either on top of an old one that
        # we're now ignoring, or as a new one
        delta.change_list[change_position] = (attr_name, attr_value)
        
    @entitymod
    def mod_transaction_with_func(self, delta, function, args, kargs):
        delta.latest_function_call = len(delta.change_list)
        delta.change_list.append( (function, args, kargs) )

    def get_entity_from_identifier(self, entity_identifier):
        # probably a good sign that TransactionCommingThread should be
        # elsewhere...
        from book import BOOKS_SUB_DB_KEY

        (book_name, trans_id) = entity_identifier
        return self.dbroot[BOOKS_SUB_DB_KEY][book_name].get_transaction(
            trans_id)
    
    def run(self):
        dbcon = self.book_set.get_new_dbcon()
        self.dbroot = dbcon.root()
        ChangeMessageRecievingThread.run(self)
        dbcon.close()

    def handle_entity_change(self, trans_delta, trans):
        trans_delta.change_list.reverse()
        while len(trans_delta.change_list) > 0:
            change = trans_delta.change_list.pop()
            if len(change) == 3:
                (function_to_call, args, kargs) = change
                function_to_call = getattr(trans, function_to_call)
                function_to_call(*args, **kargs)            
            else:
                assert( len(change) == 2 )
                (attr_name, attr_value) = change
                setattr(trans, attr_name, attr_value)
        trans_delta.attribute_change_index.clear()
        # important value, see comments above
        trans_delta.latest_function_call = -1

    def message_block_begin(self):
        transaction.get().commit()

    def message_block_end(self):
        transaction.get().commit()

class TransactionMirror(object):
    """Allows you to change a transaction being handled by a 
    TransactionComittingThread as if you had the transaction itself,
    You can set attributes, and you can call instance mutator functions
    (without access to return values), but you can *NOT* get attributes
    or get the values returned by calling instance methods
    """

    # important, any attributes that are being set must be defined here
    trans_thread = None
    book_name = None
    trans_id = None

    def __init__(self, book_name, trans_id, trans_thread):
        self.trans_thread = trans_thread
        self.book_name = book_name
        self.trans_id = trans_id
    
    def __getattribute__(self, attr_name):
        try:
            return object.__getattribute__(self, attr_name)
        except AttributeError:
            def ret_function(*args, **kargs):                
                # note the intentional lack of return
                self.trans_thread.mod_transaction_with_func(
                    (self.book_name, self.trans_id), attr_name, args, kargs)
            return ret_function

    def __setattr__(self, attr_name, value):
        # if we're setting one of the attribute from this class, set it
        # as normal
        if hasattr(self, attr_name):
            object.__setattr__(self, attr_name, value)
        # else set an attribute from the mirror class
        else:
            self.trans_thread.mod_transaction_attr(
                (self.book_name, self.trans_id), attr_name, value)
