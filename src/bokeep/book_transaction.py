# Copyright (C) 2010-2011  ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
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
# Authors: Mark Jenkins <mark@parit.ca>
#          Samuel Pauls <samuel@parit.ca>

from persistent import Persistent

class FinancialTransactionLine(object):
    """Represents a line in a balanced financial transaction.
    Each line has an amount. Positive numbers are debits, negative numbers
    are credits. The amount must be of the builtin type decimal.Decimal
    
    In addition to amount, some accounting backends allow for other
    attributes to be associated with a financial transaction line. If you set
    them on instances of this class, they will be picked up and used by
    backend plugins that support them.
    Backends that don't support particular attributes will ignore them.
    
    account_spec -- specifies an account to associate with the line;
                    will be supported by GnuCash and SerialFile backend plugins
                    The format/type of this attribute is backend plugin
                    specific, eventually, anything using this attribute should
                    be able to get an object of right tu[e simply by
                    communicating with the backend
                    plugin. (the backend plugin should also facilitate the
                    selection)
    line_memo -- specifies a string to associate with the line,
                 will be supported by GnuCash and SerialFile backend plugins

    create_account_if_missing -- if present and set to True, specifies
    that the account specified by account_spec should be created if missing
    """
    def __init__(self, amount):
        self.amount = amount

class FinancialTransaction(object):
    """Represents a balanced financial transaction, which consists of
    FinancialTransactionLine s. The amount of all the FinancialTransactionLine
    s must add up to zero. (This is what makes them balanced.)

    Extended attributes: (not required, but may be optionally specified,
    will be supported by some backends)
    
    trans_date -- specifies the date of the financial transaction, the
    date should be the one used to include or exclude the transaction from
    income statements and balance sheets. Must be a datetime.date or
    datetime.datetime object. Will be GnuCash and SerialFile backend
    plugins

    description -- a description (string) for the entire transaction.
    If the accounting backend supports it, this should be the text used for
    the name on a cheque. Will be supported by GnuCash and SerialFile backend
    plugins

    chequenum -- a number (integer) to assign if the transaction is a cheque,
    or other numberic transaction identifier. Will be supported by GnuCash
    and SerialFile backends.

    currency -- an all caps three letter ISO code for a currency
                e.g USD and CAD
    """
    def __init__(self, lines):
        self.lines = lines

def make_trans_line_pair(amount, debit_account, credit_account,
                         debit_memo='', credit_memo=''):
    """Creates the lines of a financial transaction, but not the transaction
    itself."""
    
    return [ make_fin_line(amount,
                           debit_account, debit_memo),
             make_fin_line(-amount,
                           credit_account, credit_memo) ]

def make_common_fin_trans(lines, trans_date, description,
                          currency, chequenum=None):
    """Creates a typical financial transaction."""
    
    trans = FinancialTransaction(lines)
    trans.trans_date = trans_date
    trans.description = description
    trans.currency = currency
    if chequenum != None:
        trans.chequenum = chequenum
    return trans

def make_fin_line(amount, accounts, comment, **extra_attributes):
    """Creates a transaction line."""
    
    line = FinancialTransactionLine(amount)
    line.account_spec = accounts
    line.line_memo = comment
    line.__dict__.update( extra_attributes )
    return line

class BoKeepTransactionNotMappableToFinancialTransaction(Exception):
    pass

class Transaction(Persistent):
    """A BoKeep transaction."""
    
    def __init__(self, associated_plugin):
        self.associated_plugin = associated_plugin

    def get_financial_transactions(self):
        """Return a generator that will provide FinancialTransaction instances
        associated with this bo-keep Transaction to be stored by a
        BackendModule
        """
        raise BoKeepTransactionNotMappableToFinancialTransaction()
