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
        
class TrustMoneyInTransaction(TrustTransaction):
    pass

class TrustMoneyOutTransaction(TrustTransaction):
    def get_transfer_amount(self):
        return TrustTransaction.get_transfer_amount(self) * NEG_1


