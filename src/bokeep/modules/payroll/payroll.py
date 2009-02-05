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

# bo-keep
from bokeep.book_transaction import Transaction as BookTransaction

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

    def print_accounting_lines_to_file(self, writefunc):
        writefunc('Per employee lines, payroll transaction' + '\n')
        for (debit_credit_str, debit_credit_pos, negate) in \
                (('debits', 0, Decimal(1)), ('credits', 1, Decimal(1))):
            writefunc(debit_credit_str + '\n')
            for (accounts, comment, paystub_line) in \
                    self.payday_accounting_lines[0][debit_credit_pos]:
                outstr = str(negate * decimal_from_float(paystub_line.get_value())) + str(accounts) + str(comment)
        writefunc('\n')
        writefunc('Cummulative lines, payroll transaction' + '\n')
        for (debit_credit_str, debit_credit_pos, negate) in \
                (('debits', 0, Decimal(1)), ('credits', 1, Decimal(1))):
            writefunc(debit_credit_str + '\n')
            for (id, accounts, comment), line_list in \
                    self.payday_accounting_lines[1][debit_credit_pos].\
                    iteritems():
                writefunc(str((sum( ( decimal_from_float(line.get_value())
                             for line in line_list), Decimal(0)),\
                             accounts, comment)) + '\n')
        writefunc('\n')

        writefunc('Per employee transaction lines' + '\n')
        chequenum = self.payday_accounting_lines[2]
        for trans in self.payday_accounting_lines[3:]:
            writefunc(str(trans[2]) + '\n') # employee name
            writefunc( 'chequenum ' + str(chequenum) + '\n')
            for (debit_credit_str, debit_credit_pos, negate) in \
                    (('debits', 0, Decimal(1)), ('credits', 1, Decimal(1))):
                writefunc(debit_credit_str + '\n')
                for (accounts, comment, paystub_line) in \
                        trans[debit_credit_pos]:
                    writefunc(str(negate * decimal_from_float(
                    paystub_line.get_value() )) + ' ' +\
                    str(accounts) + ' ' + comment + '\n')
            writefunc(' \n')
            chequenum = chequenum+1

    def print_accounting_lines(self):
        self.print_accounting_lines_to_file(sys.stdout.write)
