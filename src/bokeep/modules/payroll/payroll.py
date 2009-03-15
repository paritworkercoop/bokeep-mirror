# python
from decimal import Decimal

import sys

# cndpayroll
from cdnpayroll.payday import Payday as cdnpayroll_Payday
from cdnpayroll.paystub import Paystub
from cdnpayroll.employee import Employee
from cdnpayroll.paystub_line import \
    PaystubLine, PaystubIncomeLine, PaystubWageLine, PaystubOvertimeWageLine, \
    PaystubCalculatedLine, PaystubDeductionLine, PaystubSimpleDeductionLine, \
    PaystubCalculatedDeductionLine, PaystubEmployerContributionLine, \
    PaystubCalculatedEmployerContributionLine, \
    PaystubSummaryLine, PaystubNetPaySummaryLine, PaystubTotalIncomeLine, \
    PaystubMultipleOfIncomeLine, PaystubDeductionMultipleOfIncomeLine, \
    PaystubEmployerContributionMultipleOfIncomeLine
from cdnpayroll.cpp import \
    PaystubCPPDeductionLine, PaystubCPPEmployerContributionLine
from cdnpayroll.ei import \
    PaystubEIDeductionLine, PaystubEIEmployerContributionLine
from cdnpayroll.income_tax import \
    PaystubIncomeTaxDeductionLine, PaystubExtraIncomeTaxDeductionLine, \
    PaystubCalculatedIncomeTaxDeductionLine
from cdnpayroll.vacation_pay import PaystubVacpayLine

# bo-keep
from bokeep.book_transaction import \
    Transaction as BookTransaction, \
    BoKeepTransactionNotMappableToFinancialTransaction, \
    FinancialTransactionLine, FinancialTransaction, make_fin_line

# subclass and override functions from cdnpayroll classes to be persistable
# via zopedb, and to use each other instead of original cdnpayroll classes

def decimal_from_float(float_value):
    return Decimal('%.2f' % float_value)

class Payday(BookTransaction, cdnpayroll_Payday):
    def __init__(self, paydate):
        BookTransaction.__init__(self)
        cdnpayroll_Payday.__init__(self, paydate)
        self._p_changed = True

    def add_paystub(self, paystub):
        cdnpayroll_Payday.add_paystub(self, paystub)
        self._p_changed = True

    def specify_accounting_lines(self, payday_accounting_lines):
        self.payday_accounting_lines = payday_accounting_lines
        self._p_changed = True


    def get_financial_transactions(self):
        """Generate one big transaction for the payroll, and a transaction
        for each employee.

        This is based on the specification attribute, payday_accounting_lines
        If that attribute isn't set, this function is unable to generate a
        transaction
        """
        if not hasattr(self, 'payday_accounting_lines'):
            raise BoKeepTransactionNotMappableToFinancialTransaction()
        
        # Per employee lines, payroll transaction 
        fin_lines = []
        for (debit_credit_pos, negate) in \
                ((0, Decimal(1)), (1, Decimal(-1))): # debits then credits
            fin_lines.extend( 
                make_fin_line(
                    negate * decimal_from_float(paystub_line.get_value()),
                    accounts, comment)
                for (accounts, comment, paystub_line) in \
                self.payday_accounting_lines[0][debit_credit_pos]
                )

        # Cummulative lines, payroll transaction
        for (debit_credit_pos, negate) in \
                ( (0, Decimal(1)), (1, Decimal(-1)) ): # debits then credits
            fin_lines.extend(
                make_fin_line(
                    negate * 
                    sum( ( decimal_from_float(line.get_value())
                           for line in line_list),
                         Decimal(0) ),
                    accounts,
                    comment
                )
                
                for (id, accounts, comment), line_list in \
                    self.payday_accounting_lines[1][debit_credit_pos].\
                    iteritems()
                )
        
        fin_trans = FinancialTransaction(fin_lines)
        fin_trans.trans_date = self.paydate
        fin_trans.description = "payroll"
        yield fin_trans

        # Per employee transactions
        chequenum = self.payday_accounting_lines[2]
        for trans in self.payday_accounting_lines[3:]:
            fin_lines = []
            for (debit_credit_pos, negate) in \
                    ((0, Decimal(1)), (1, Decimal(-1))): # debits then credits
                fin_lines.extend( 
                    make_fin_line(
                        negate * decimal_from_float(
                            paystub_line.get_value() ),
                        accounts,
                        comment )                        
                    for (accounts, comment, paystub_line) in \
                        trans[debit_credit_pos]
                    )
            fin_trans = FinancialTransaction(fin_lines)
            fin_trans.trans_date = self.paydate
            fin_trans.description = trans[2]
            fin_trans.chequenum = chequenum
            chequenum = chequenum+1
            yield fin_trans

    def print_accounting_lines(self):
        self.print_accounting_lines_to_file(sys.stdout.write)
