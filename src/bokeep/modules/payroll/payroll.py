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

from bokeep.book_transaction import Transaction as BookTransaction

from persistent import Persistent


# subclass and override functions from cdnpayroll classes to be persistable
# via zopedb, and to use each other instead of original cdnpayroll classes

class Payday(BookTransaction, cdnpayroll_Payday):
    def __init__(self, paydate):
        BookTransaction.__init__(self)
        cdnpayroll_Payday.__init__(self, paydate)
        self._p_changed = True

    def add_paystub(self, paystub):
        cdnpayroll_Payday.add_paystub(self, paystub)
        self._p_changed = True

    def specify_account_mapping(self, double_entry_accounting_spec):
        self._v_double_entry_accounting_spec = double_entry_accounting_spec
        self._p_changed = True

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


