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
from decimal import Decimal
from datetime import datetime
from bokeep.book_transaction import \
    Transaction, FinancialTransaction, FinancialTransactionLine, \
    BoKeepTransactionNotMappableToFinancialTransaction

ZERO = Decimal(0)
NEG_1 = Decimal(-1)

class TrustTransaction(Transaction):
    def __init__(self):
        self.transfer_amount = Decimal(0)
        self.trustor = None
        self.trans_date = datetime.today()

    def get_financial_transactions(self):
        # you should throw BoKeepTransactionNotMappableToFinancialTransaction
        # under some conditions
        return FinancialTransaction(
            (FinancialTransactionLine(self.get_transfer_amount()),
             FinancialTranactionLine(self.get_transfer_amount() * NEG_1) )
            )

    def get_transfer_amount(self):
        return self.transfer_amount

    def set_trustor(self, trustor):
        self.trustor = trustor

    def get_trustor(self):
        return self.trustor

    def get_displayable_amount(self):
        return TrustTransaction.get_transfer_amount(self)

        
class TrustMoneyInTransaction(TrustTransaction):
    pass

class TrustMoneyOutTransaction(TrustTransaction):
    def get_transfer_amount(self):
        return TrustTransaction.get_transfer_amount(self) * NEG_1
