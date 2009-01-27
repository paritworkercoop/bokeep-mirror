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
        cdnpayroll_PaystubCalculatedEmployerContributionLine
from cdnpayroll.cpp import \
    PaystubCPPDeductionLine as cdnpayroll_PaystubCPPDeductionLine, \
    PaystubCPPEmployerContributionLine as \
        cdnpayroll_PaystubCPPEmployerContributionLine
from cdnpayroll.ei import \
    PaystubEIDeductionLine as cdnpayroll_PaystubEIDeductionLine, \
    PaystubEIEmployerContributionLine as \
        cdnpayroll_PaystubEIEmployerContributionLine
from cdnpayroll.income_tax import \
    PaystubCalculatedIncomeTaxDeductionLine as \
        cdnpayroll_PaystubCalculatedIncomeTaxDeductionLine

# bo-keep
from bokeep.book_transaction import Transaction as BookTransaction

def lines_of_class_function(class_find):
    def new_func(paystub):
        return paystub.get_paystub_lines_of_class(class_find)
    return new_func

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

class PaystubLine(Persistent, cdnpayroll_PaystubLine):
    pass

class PaystubIncomeLine(Persistent, cdnpayroll_PaystubIncomeLine):
    pass

class PaystubWageLine(Persistent, cdnpayroll_PaystubWageLine):
    pass

class PaystubOvertimeWageLine(Persistent,
                              cdnpayroll_PaystubOvertimeWageLine):
    pass

class PaystubCalculatedLine(Persistent, cdnpayroll_PaystubCalculatedLine):
    pass

class PaystubDeductionLine(Persistent, cdnpayroll_PaystubDeductionLine):
    pass

class PaystubSimpleDeductionLine(Persistent,
                                 cdnpayroll_PaystubSimpleDeductionLine):
    pass

class PaystubCalculatedDeductionLine(Persistent,
                                     cdnpayroll_PaystubCalculatedDeductionLine):
    pass

class PaystubEmployerContributionLine(
    Persistent,
    cdnpayroll_PaystubEmployerContributionLine):
    pass

class PaystubCalculatedEmployerContributionLine(
    Persistent, 
    cdnpayroll_PaystubCalculatedEmployerContributionLine):
    pass

class PaystubCPPDeductionLine(Persistent, cdnpayroll_PaystubCPPDeductionLine):
    pass

class PaystubCPPEmployerContributionLine(
    Persistent,
    cdnpayroll_PaystubCPPEmployerContributionLine):
    pass

class PaystubEIDeductionLine(
    Persistent,
    cdnpayroll_PaystubEIDeductionLine):
    pass

class PaystubEIEmployerContributionLine(
    Persistent,
    cdnpayroll_PaystubEIEmployerContributionLine):
    pass

class PaystubCalculatedIncomeTaxDeductionLine(
    Persistent,
    cdnpayroll_PaystubCalculatedIncomeTaxDeductionLine
    ):
    pass
    
class Employee(Persistent, cdnpayroll_Employee):
    auto_add_lines = [
        PaystubCPPDeductionLine,
        PaystubCPPEmployerContributionLine,
        PaystubEIDeductionLine,
        PaystubEIEmployerContributionLine,
        PaystubCalculatedIncomeTaxDeductionLine,
        ]

    def add_paystub(self, paystub):
        cdnpayroll_Employee.add_paystub(self, paystub)
        self._p_changed = True

    def create_and_add_new_paystub(self, payday):
        return Paystub(self, payday)


