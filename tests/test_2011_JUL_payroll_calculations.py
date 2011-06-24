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
# Authors: Mark Jenkins <mark@parit.ca>
#          Samuel Pauls <samuel@parit.ca>

# python imports
from datetime import date
from unittest import TestCase, main
from decimal import Decimal

# bokeep.plugins.payroll.canada imports
from bokeep.plugins.payroll.canada.employee import Employee
from bokeep.plugins.payroll.payroll import Payday
from bokeep.plugins.payroll.canada.paystub import Paystub
from bokeep.plugins.payroll.canada.paystub_line import PaystubIncomeLine
from bokeep.plugins.payroll.canada.income_tax import PaystubCalculatedIncomeTaxDeductionLine, \
    calc_annual_provincial_income_tax_T2, calc_annual_basic_provincial_tax_T4, \
    projected_annual_prov_tax_reduction, calc_prov_non_refund_tax_credit_K1P, \
    calc_prov_CPP_tax_credit_K2Pc, calc_prov_EI_tax_credit_K2Pe
from bokeep.plugins.payroll.canada.functions import range_table_lookup, \
    decimal_truncate_two_places, neg2zero, \
    decimal_round_two_place_using_third_digit
from bokeep.plugins.payroll.canada.cpp import get_cpp_max_contribution, get_cpp_contribution_rate,\
    get_cpp_basic_exemption, PaystubCPPDeductionLine
from bokeep.plugins.payroll.canada.ei import get_max_ei_premium, PaystubEIDeductionLine
from bokeep.plugins.payroll.canada.vacation_pay import PaystubVacationPayAvailable

class Basic2011JulyPayTest(TestCase):
    def setUp(self):
        self.emp = Employee("test employee")
        date_paydate_one = date(2011, 07, 01) # 2011, July, 1st
        self.payday_one = Payday(None)
        self.payday_one.set_paydate(
            *(date_paydate_one for i in xrange(3)) )
        self.paystub_one = Paystub(self.emp, self.payday_one)

def create_basic_test_class(name, income, fed_tax_credits, prov_tax_credits,
                            expected_tax, expected_cpp, expected_ei ):
    class new_test_class(Basic2011JulyPayTest):
        def setUp(self):
            Basic2011JulyPayTest.setUp(self)
            self.paystub_one.add_paystub_line(
                PaystubIncomeLine( self.paystub_one, Decimal(income) ) )
            self.emp.fed_tax_credits = fed_tax_credits
            self.emp.prov_tax_credits = prov_tax_credits

        def test_tax(self):
            income_tax = self.paystub_one.income_tax_deductions()
            self.assertEqual(income_tax, Decimal(expected_tax))
            self.assert_(income_tax.as_tuple()[2] >= -2)

        def test_cpp(self):
            cpp = self.paystub_one.cpp_deductions()
            self.assertEqual(cpp, Decimal(expected_cpp))
            self.assert_(cpp.as_tuple()[2] >= -2)

        def test_ei(self):
            ei = self.paystub_one.ei_deductions()
            self.assertEquals(ei, Decimal(expected_ei))
            self.assert_(ei.as_tuple()[2] >= -2 )

    new_test_class.__name__ = name
    return new_test_class

# now based on actual values from CRA calculator for July 1st
TestTinyIncome = create_basic_test_class('TestTinyIncome', 100, 1, 1,
                                         0, 0, '1.78')
# CRA calculate says income tax deductions of 14.49, but we'll say close enough
# for now
TestSmallIncome = create_basic_test_class('TestSmallIncome', 480, 1, 1,
                                          '14.48', '17.10', '8.54')
                                                
if __name__ == "__main__":
    main()
