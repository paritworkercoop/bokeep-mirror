# python
from decimal import Decimal

# zopedb
from persistent import Persistent

# cndpayroll
from cdnpayroll.payday import Payday as cdnpayroll_Payday
from cdnpayroll.paystub import Paystub as cdnpayroll_Paystub
from cdnpayroll.employee import Employee as cdnpayroll_Employee
from cdnpayroll.paystub_line import \
    PaystubLine as cdnpayroll_PaystubLine, \
    PaystubIncomeLine as cdnpayroll_PaystubIncomeLine, \
    PaystubWageLine as cdnpayroll_PaystubWageLine, \
    PaystubOvertimeWageLine as cdnpayroll_PaystubOvertimeWageLine, \
    PaystubCalculatedLine as cdnpayroll_PaystubCalculatedLine, \
    PaystubDeductionLine as cdnpayroll_PaystubDeductionLine, \
    PaystubSimpleDeductionLine as cdnpayroll_PaystubSimpleDeductionLine, \
    PaystubCalculatedDeductionLine as \
    cdnpayroll_PaystubCalculatedDeductionLine, \
    PaystubEmployerContributionLine as \
    cdnpayroll_PaystubEmployerContributionLine, \
    PaystubCalculatedEmployerContributionLine as \
    cdnpayroll_PaystubCalculatedEmployerContributionLine, \
    PaystubSummaryLine as cdnpayroll_PaystubSummaryLine, \
    PaystubNetPaySummaryLine as cdnpayroll_PaystubNetPaySummaryLine, \
    PaystubTotalIncomeLine as cdnpayroll_PaystubTotalIncomeLine, \
    PaystubMultipleOfIncomeLine as cdnpayroll_PaystubMultipleOfIncomeLine, \
    PaystubDeductionMultipleOfIncomeLine as \
    cdnpayroll_PaystubDeductionMultipleOfIncomeLine, \
    PaystubEmployerContributionMultipleOfIncomeLine as \
    cdnpayroll_PaystubEmployerContributionMultipleOfIncomeLine

from cdnpayroll.cpp import \
    PaystubCPPDeductionLine as cdnpayroll_PaystubCPPDeductionLine, \
    PaystubCPPEmployerContributionLine as \
        cdnpayroll_PaystubCPPEmployerContributionLine
from cdnpayroll.ei import \
    PaystubEIDeductionLine as cdnpayroll_PaystubEIDeductionLine, \
    PaystubEIEmployerContributionLine as \
        cdnpayroll_PaystubEIEmployerContributionLine
from cdnpayroll.income_tax import \
    PaystubIncomeTaxDeductionLine as \
    cdnpayroll_PaystubIncomeTaxDeductionLine, \
    PaystubExtraIncomeTaxDeductionLine as \
    cdnpayroll_PaystubExtraIncomeTaxDeductionLine, \
    PaystubCalculatedIncomeTaxDeductionLine as \
    cdnpayroll_PaystubCalculatedIncomeTaxDeductionLine

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

    def print_accounting_lines(self):
        print 'Per employee lines, payroll transaction'
        for (debit_credit_str, debit_credit_pos, negate) in \
                (('debits', 0, Decimal(1)), ('credits', 1, Decimal(1))):
            print debit_credit_str
            for (accounts, comment, paystub_line) in \
                    self.payday_accounting_lines[0][debit_credit_pos]:
                print negate * decimal_from_float(paystub_line.get_value()), \
                    accounts, comment
        print ''

        print 'Cummulative lines, payroll transaction'
        for (debit_credit_str, debit_credit_pos, negate) in \
                (('debits', 0, Decimal(1)), ('credits', 1, Decimal(1))):
            print debit_credit_str
            for (id, accounts, comment), line_list in \
                    self.payday_accounting_lines[1][debit_credit_pos].\
                    iteritems():
                print sum( ( decimal_from_float(line.get_value())
                             for line in line_list), Decimal(0)),\
                             accounts, comment
        print ''

        #print 'Per employee transaction lines'
        #for (debit_credit_str, debit_credit_pos, negate) in \
        #        (('debits', 0, Decimal(1)), ('credits', 1, Decimal(1))):
        #    print debit_credit_str
        #    for (accounts, comment, paystub_line) in \
        #            self.payday_accounting_lines[1][debit_credit_pos]:
        #        print negate * decimal_from_float(
        #            paystub_line.get_value() ), \
        #            accounts, comment
        #print ' '

class Paystub(Persistent, cdnpayroll_Paystub):
    def add_paystub_line(self, paystub_line):
        cdnpayroll_Paystub.add_paystub_line(self, paystub_line)
        self._p_changed = True

class PaystubLine(cdnpayroll_PaystubLine):
    pass

class PaystubLinePersist(Persistent, PaystubLine):
    pass

class PaystubSummaryLine(cdnpayroll_PaystubSummaryLine, PaystubLine):
    pass

class PaystubSummaryLinePersist(Persistent, PaystubSummaryLine):
    pass

class PaystubNetPaySummaryLine(cdnpayroll_PaystubNetPaySummaryLine,
                               PaystubSummaryLine):
    pass

class PaystubNetPaySummaryLinePersist(Persistent,
                                      PaystubNetPaySummaryLine):
    pass

class PaystubTotalIncomeLine(cdnpayroll_PaystubTotalIncomeLine,
                             PaystubSummaryLine):
    pass

class PaystubTotalIncomeLinePersist(Persistent, PaystubTotalIncomeLine):
    pass

class PaystubIncomeLine(cdnpayroll_PaystubIncomeLine, PaystubLine):
    pass

class PaystubIncomeLinePersist(Persistent, PaystubIncomeLine):
    pass

class PaystubWageLine(cdnpayroll_PaystubWageLine, PaystubIncomeLine):
    pass

class PaystubWageLinePersist(Persistent, PaystubWageLine):
    pass

class PaystubOvertimeWageLine(cdnpayroll_PaystubOvertimeWageLine,
                              PaystubWageLine ):
    pass

class PaystubOvertimeWageLinePersist(Persistent,
                                     PaystubOvertimeWageLine):
    pass

class PaystubCalculatedLine(cdnpayroll_PaystubCalculatedLine,
                            PaystubLine):
    pass

class PaystubCalculatedLinePersist(Persistent, PaystubCalculatedLine):
    pass

class PaystubDeductionLine(cdnpayroll_PaystubDeductionLine,
                           PaystubLine):
    pass

class PaystubDeductionLinePersist(Persistent, PaystubDeductionLine):
    pass

class PaystubSimpleDeductionLine(cdnpayroll_PaystubSimpleDeductionLine,
                                 PaystubDeductionLine):
    pass

class PaystubSimpleDeductionLinePersist(
    Persistent,
    PaystubSimpleDeductionLine):
    pass

class PaystubCalculatedDeductionLine(
    cdnpayroll_PaystubCalculatedDeductionLine,
    PaystubCalculatedLine,
    PaystubDeductionLine):
    pass

class PaystubCalculatedDeductionLinePersist(
    Persistent,
    PaystubCalculatedDeductionLine):
    pass

class PaystubEmployerContributionLine(
    cdnpayroll_PaystubEmployerContributionLine,
    PaystubLine):
    pass

class PaystubEmployerContributionLinePersist(
    Persistent,
    PaystubEmployerContributionLine):
    pass

class PaystubCalculatedEmployerContributionLine(
    cdnpayroll_PaystubCalculatedEmployerContributionLine,
    PaystubCalculatedLine, PaystubEmployerContributionLine):
    pass

class PaystubCalculatedEmployerContributionLinePersist(
    Persistent, 
    PaystubCalculatedEmployerContributionLine):
    pass

class PaystubCPPDeductionLine(
    cdnpayroll_PaystubCPPDeductionLine,
    PaystubCalculatedDeductionLine):
    pass

class PaystubCPPDeductionLinePersist(Persistent, PaystubCPPDeductionLine):
    pass

class PaystubCPPEmployerContributionLine(
    cdnpayroll_PaystubCPPEmployerContributionLine,
    PaystubCalculatedEmployerContributionLine):
    pass

class PaystubCPPEmployerContributionLinePersist(
    Persistent,
    PaystubCPPEmployerContributionLine):
    pass

class PaystubEIDeductionLine(
    cdnpayroll_PaystubEIDeductionLine,
    PaystubCalculatedDeductionLine):
    pass

class PaystubEIDeductionLinePersist(
    Persistent,
    PaystubEIDeductionLine):
    pass

class PaystubEIEmployerContributionLine(
    cdnpayroll_PaystubEIEmployerContributionLine,
    PaystubCalculatedEmployerContributionLine):
    pass

class PaystubEIEmployerContributionLinePersist(
    Persistent,
    PaystubEIEmployerContributionLine):
    pass

class PaystubCalculatedIncomeTaxDeductionLine(
    cdnpayroll_PaystubCalculatedIncomeTaxDeductionLine,
    PaystubDeductionLine
    ):
    pass

class PaystubCalculatedIncomeTaxDeductionLinePersist(
    Persistent,
    PaystubCalculatedIncomeTaxDeductionLine
    ):
    pass

class PaystubMultipleOfIncomeLine(cdnpayroll_PaystubMultipleOfIncomeLine,
                                  PaystubCalculatedLine):
    pass

class PaystubMultipleOfIncomeLinePersist(Persistent,
                                         PaystubMultipleOfIncomeLine):
    pass

class PaystubDeductionMultipleOfIncomeLine(
    cdnpayroll_PaystubDeductionMultipleOfIncomeLine,
    PaystubMultipleOfIncomeLine,
    PaystubDeductionLine):
    pass

class PaystubDeductionMultipleOfIncomeLinePersist(
    Persistent, PaystubDeductionMultipleOfIncomeLine):
    pass

class PaystubEmployerContributionMultipleOfIncomeLine(
    cdnpayroll_PaystubEmployerContributionMultipleOfIncomeLine,
    PaystubMultipleOfIncomeLine,
    PaystubEmployerContributionLine):
    pass

class PaystubEmployerContributionMultipleOfIncomeLinePersist(
    Persistent,
    PaystubEmployerContributionMultipleOfIncomeLine):
    pass

class Employee(Persistent, cdnpayroll_Employee):
    auto_add_lines = [
        PaystubCPPDeductionLinePersist,
        PaystubCPPEmployerContributionLinePersist,
        PaystubEIDeductionLinePersist,
        PaystubEIEmployerContributionLinePersist,
        PaystubCalculatedIncomeTaxDeductionLinePersist,
        ]

    def add_paystub(self, paystub):
        cdnpayroll_Employee.add_paystub(self, paystub)
        self._p_changed = True

    def create_and_add_new_paystub(self, payday):
        return Paystub(self, payday)


