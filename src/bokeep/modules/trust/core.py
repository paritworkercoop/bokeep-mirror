from decimal import Decimal

from bokeep.book_transaction import \
    Transaction, FinancialTransaction, FinancialTransactionLine, \
    BoKeepTransactionNotMappableToFinancialTransaction

ZERO = Decimal(0)
NEG_1 = Decimal(-1)

class TrustTransaction(Transaction):
    def __init__(self):
        self.transfer_amount = Decimal(0)

    def get_financial_transactions(self):
        return FinancialTransaction(
            (FinancialTransactionLine(self.get_transfer_amount()),
             FinancialTranactionLine(self.get_transfer_amount() * NEG_1) )
            )

    def get_transfer_amount(self):
        return self.transfer_amount

class TrustMoneyInTransaction(TrustTransaction):
    pass

class TrustMoneyOutTransaction(TrustTransaction):
    def get_transfer_amount(self):
        return TrustTransaction.get_transfer_amount(self) * NEG_ONE


