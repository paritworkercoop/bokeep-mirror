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
# Author: Jamie Campbell <jamie@parit.ca>
# Author: Mark Jenkins <mark@parit.ca>
# Author: Samuel Pauls <samuel@parit.ca>

from decimal import Decimal
from datetime import datetime
from bokeep.book_transaction import \
    Transaction, FinancialTransaction, FinancialTransactionLine, \
    BoKeepTransactionNotMappableToFinancialTransaction

ZERO = Decimal(0)
NEG_1 = Decimal(-1)

class TrustTransaction(Transaction):
    def __init__(self, trust_module):
        self.trust_module = trust_module
        self.transfer_amount = Decimal(0)
        if len(trust_module.get_trustors().values()) == 0:
            self.trustor = None
        else:
            self.trustor = trust_module.get_trustors().values()[0].name
        self.memo = ''
        self.trans_date = datetime.today()
        self.set_id(-1)

    def get_financial_transactions(self):
        # you should throw BoKeepTransactionNotMappableToFinancialTransaction
        # under some conditions
        cash_line = FinancialTransactionLine(self.get_transfer_amount())
        if hasattr(self.trust_module, 'cash_account'):
            cash_line.account_spec = self.trust_module.cash_account

        #use the cash line's memo field for the memo
        cash_line.line_memo = self.memo

        liability_line = \
            FinancialTransactionLine(self.get_transfer_amount() * NEG_1)
        if hasattr(self.trust_module, 'trust_liability_account'):
            if self.get_trustor_name() == None:
                liability_line.account_spec = \
                    self.trust_module.trust_liability_account
            else:
                liability_line.set_create_account_if_missing(True)
                liability_line.account_spec = \
                    self.trust_module.trust_liability_account + \
                    (self.get_trustor_name(),)
        fin_trans = FinancialTransaction( (cash_line, liability_line) )
        if self.trustor != None:
            # this should never be so, yet in the unit tests it comes up
            if isinstance(self.trustor, str):
                fin_trans.description = self.trustor
            else:
                fin_trans.description = self.trustor.name
        fin_trans.trans_date = self.trans_date
        fin_trans.chequenum = self.__id
        fin_trans.currency = self.trust_module.get_currency()
        # should add chequenum at some point, legal aid requested this
        # for ordering
        return ( fin_trans, )

    def get_transfer_amount(self):
        return self.transfer_amount

    def set_trustor_name(self, trustor):
        assert(trustor == None or trustor.__class__ == str)
        self.trustor = trustor
        
    def set_id(self, id):
        """Sets the ID of this trust transaction.  It's used as the ID in the
        backend, or as the GnuCash plugin would call it, the chequenum."""
        self.__id = id

    def get_trustor_name(self):
        return self.trustor

    def get_displayable_amount(self):
        return TrustTransaction.get_transfer_amount(self)

    def get_memo(self):
        return self.memo

        
class TrustMoneyInTransaction(TrustTransaction):
    pass

class TrustMoneyOutTransaction(TrustTransaction):
    def get_transfer_amount(self):
        # when Trust money is paid out, the cash line needs to be negative
        # (credit) and the liability line needs to be positive (debit)
        # see TrustTransaction.get_financial_transactions
        return TrustTransaction.get_transfer_amount(self) * NEG_1

