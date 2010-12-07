# paystub.py
# Copyright (C) 2006 ParIT Worker Co-operative <paritinfo@parit.ca>
# Copyright (C) 2001-2006 Paul Evans <pevans@catholic.org>
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# Author(s): Mark Jenkins <mark@parit.ca>
#            Paul Evans <pevans@catholic.org>

from paystub_line import \
     PaystubIncomeLine, PaystubDeductionLine, \
     PaystubCalculatedLine, \
     PaystubEmployerContributionLine, \
     sum_paystub_lines, sum_paystub_lines_for_net_pay, \
     filter_for_taxable_lines, filter_for_tax_exempt_lines

from income_tax import PaystubIncomeTaxDeductionLine
from cpp import PaystubCPPDeductionLine, PaystubCPPEmployerContributionLine
from ei import PaystubEIDeductionLine, PaystubEIEmployerContributionLine

from functions import neg2zero, filter_by_class, filter_by_not_class, \
    instance_of_one
from decimal import Decimal

from itertools import chain

# zopedb
from persistent import Persistent

class Paystub(Persistent):
    """Encapsulates all the details of an Employee's paystub on a payday.

    Attributes:

    employee -- The employee being paid.
    paystub_lines -- PaystubLine objects associated with this paystub
    calculated_lines -- True once the calculated lines have been added
    """
    calculated_lines = False

    def __init__(self, employee, payday):
        self.employee = employee
        self.paystub_lines = []
        self.payday = payday       
        self.payday.add_paystub(self)
        self.employee.add_paystub(self)

        # Add the automatically added lines
        for paystub_line_class in self.employee.auto_add_lines:
            self.add_new_paystub_line_of_class(paystub_line_class)

    def add_paystub_line(self, paystub_line):
        self.paystub_lines.append( paystub_line )
        self._p_changed = True

    def add_new_paystub_line_of_class(self, paystub_line_class):
        return self.add_paystub_line(paystub_line_class(self) )

    def get_paystub_lines_of_class(self, paystub_line_class):
        """A list of all paystub lines of a certain class
        """
        return filter_by_class(paystub_line_class, self.paystub_lines)

    def get_paystub_lines_of_classes_not_classes(
        self,
        good_classes, bad_classes):
        return ( line
                 for line in self.paystub_lines
                 if instance_of_one(line, good_classes) and \
                     not instance_of_one(line, bad_classes) )

    def get_paystub_lines_not_of_class(self, paystub_line_class):
        return filter_by_not_class(paystub_line_class, self.paystub_lines)

    def get_calculated_lines(self):
        return self.get_paystub_lines_of_class(PaystubCalculatedLine)

    def get_not_calculated_lines(self):
        return self.get_paystub_lines_not_of_class(PaystubCalculatedLine)

    def get_income_lines(self):
        """A list of paystub lines that are income
        """
        return self.get_paystub_lines_of_class(PaystubIncomeLine)

    def get_cpp_deduction_lines(self):
        """A list of paystub lines that are CPP deductions
        """
        return self.get_paystub_lines_of_class(PaystubCPPDeductionLine)

    def get_cpp_contribution_lines(self):
        return self.get_paystub_lines_of_class(
            PaystubCPPEmployerContributionLine)

    def get_ei_deduction_lines(self):
        """A list of paystub lines that are EI deductions
        """
        return self.get_paystub_lines_of_class(PaystubEIDeductionLine)

    def get_ei_contribution_lines(self):
        return self.get_paystub_lines_of_class(
            PaystubEIEmployerContributionLine)

    def get_deduction_lines(self):
        """A list of paystub lines that are deductions
        """
        return self.get_paystub_lines_of_class(PaystubDeductionLine)

    def get_contribution_lines(self):
        return self.get_paystub_lines_of_class(
            PaystubEmployerContributionLine)
    
    def get_income_tax_deduction_lines(self):
        """A list of paystub lines that are income tax deductions
        """
        return self.get_paystub_lines_of_class(
            PaystubIncomeTaxDeductionLine)
    
    def get_tax_except_deduction_lines(self):
        """A list of paystub lines that are deductions that are excempt from
        taxation, such as union dues
        """
        return filter_for_tax_exempt_lines(self.get_deduction_lines())

    def get_taxable_income_lines(self):
        return filter_for_taxable_lines(self.get_income_lines())

    def income_tax_deductions(self):
        return sum_paystub_lines( self.get_income_tax_deduction_lines() )

    def cpp_deductions(self):
        """The total CPP deductions on this paystub
        """
        return sum_paystub_lines(self.get_cpp_deduction_lines())

    def ei_deductions(self):
        """The total EI deductions on this paystub
        """
        return sum_paystub_lines(self.get_ei_deduction_lines())
    
    def employer_ei_contributions(self):
        """The total EI deductions on this paystub
        """
        return sum_paystub_lines(self.get_ei_contribution_lines())

    def employer_cpp_contributions(self):
        return sum_paystub_lines(self.get_cpp_contribution_lines())

    def gross_income(self):
        """The gross income for this pay period
        """
        return sum_paystub_lines(self.get_income_lines())

    def net_pay(self):
        return sum_paystub_lines_for_net_pay( self.paystub_lines )

    def deductions(self):
        return sum_paystub_lines(self.get_deduction_lines() )

    def employer_contributions(self):
        return sum_paystub_lines(self.get_contribution_lines())

    def taxable_income(self):
        """Income from this payperiod that is taxable. This consists of
        all taxable income minus tax exempt deductions such as RRSP
        contributions, alimony, and union dues.
        """
        return sum_paystub_lines_for_net_pay(
            chain(self.get_taxable_income_lines(),
                  self.get_tax_except_deduction_lines() ) )
    
    def projected_annual_taxable_income_A(self):
        """A projection of the employee's annual taxable income.

        This is calculated by taking this paystub's taxable income,
        projecting it over a year, and subtracting any annual income
        reductions, such as the annual reduction for living in a prescribed
        zone (HD) or other kinds of annual reductions to taxable income
        """
        A = self.taxable_income()*self.employee.payperiods_P - \
            self.employee.sum_annual_income_deductions()
        # convert negatives to 0, taxable incomes can not be negative
        A = neg2zero(A)
        return A


    def __str__(self):
        strform = "Paystub for " + str(self.employee) + ", pay date " + \
            str(self.payday.paydate) + '\n'
        strform += "vvvvvvvvPaystub Linesvvvvvvvv\n"
        for payline in self.paystub_lines:
            strform += str(payline) + '\n'
        strform += "^^^^^^^^Paystub Lines^^^^^^^^\n"
        return strform
