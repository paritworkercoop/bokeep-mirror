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

class Basic2010PayTest(TestCase):
    def setUp(self):
        self.emp = Employee("test employee")
        date_paydate_one = date(2010, 01, 01)
        self.payday_one = Payday(None)
        self.payday_one.set_paydate(
            *(date_paydate_one for i in xrange(3)) )
        self.paystub_one = Paystub(self.emp, self.payday_one)

def create_basic_test_class(name, income, fed_tax_credits, prov_tax_credits,
                            expected_tax, expected_cpp, expected_ei ):
    class new_test_class(Basic2010PayTest):
        def setUp(self):
            Basic2010PayTest.setUp(self)
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


TestTinyIncome = create_basic_test_class('TestTinyIncome', 100, 1, 1,
                                         0, 0, '1.73')
TestSmallIncome = create_basic_test_class('TestSmallIncome', 480, 1, 1,
                                          '17.54', '17.10', '8.30')

class TestCarryOverYear(TestCase):
    def setUp(self):
        self.emp = Employee("test employee")
        date_paydate_one = date(2009, 12, 15)
        self.payday_one = Payday(None)
        self.payday_one.set_paydate(
            *(date_paydate_one for i in xrange(3)) )
        self.paystub_one = Paystub(self.emp, self.payday_one)
        self.paystub_one.add_paystub_line(
            PaystubIncomeLine( self.paystub_one, Decimal(480) ) )

        # override the basic tax credits to 2009 values
        self.emp.fed_tax_credits = { 'basic personal amount':
                                         Decimal(10375) }
        self.emp.prov_tax_credits = {'basic personal amount':
                                     Decimal(8134) }
        for income_tax_line in \
                self.paystub_one.get_income_tax_deduction_lines():
            income_tax_line.freeze_value()

        # return the basic tax credits to 2010 values
        self.emp.fed_tax_credits = 1
        self.emp.prov_tax_credits = 1

        date_paydate_two = date(2010, 01, 03)
        self.payday_two = Payday(None)
        self.payday_two.set_paydate(
            *(date_paydate_two for i in xrange(3)) )
        self.paystub_two = Paystub(self.emp, self.payday_two)
        self.paystub_two.add_paystub_line(
            PaystubIncomeLine( self.paystub_two, Decimal(480) ) )


    def test_PaystubVacationPayAvail(self):
        avail_line = PaystubVacationPayAvailable(self.paystub_two)
        self.paystub_two.add_paystub_line(avail_line)
        self.assertEquals(avail_line.get_value(), Decimal('38.40') )

    def test_CPP_YTD_2009(self):
        self.assertEquals(self.emp.get_cpp_YTD(self.paystub_one),
                          Decimal('0.00') )
        self.assertEquals(self.emp.get_YTD_sum_of_paystub_line_class(
                PaystubCPPDeductionLine, self.paystub_one, True),
                          Decimal('17.10') )

    def test_CPP_YTD_2010(self):
        self.assertEquals(self.emp.get_cpp_YTD(self.paystub_two),
                          Decimal('0.00') )
        self.assertEquals(self.emp.get_YTD_sum_of_paystub_line_class(
                PaystubCPPDeductionLine, self.paystub_two, True),
                          Decimal('17.10') )

    def test_EI_YTD_2009(self):
        self.assertEquals(self.emp.get_ei_YTD(self.paystub_one),
                          Decimal('0.00') )
        self.assertEquals(self.emp.get_YTD_sum_of_paystub_line_class(
                PaystubEIDeductionLine, self.paystub_one, True),
                          Decimal('8.30') )      

    def test_EI_YTD_2010(self):
        self.assertEquals(self.emp.get_ei_YTD(self.paystub_two),
                          Decimal('0.00') )
        self.assertEquals(self.emp.get_YTD_sum_of_paystub_line_class(
                PaystubEIDeductionLine, self.paystub_two, True),
                          Decimal('8.30') )      

class TestEachPart(Basic2010PayTest):
    def setUp(self):
        Basic2010PayTest.setUp(self)
        self.paystub_one.add_paystub_line(
            PaystubIncomeLine( self.paystub_one, Decimal(480) ) )
        self.emp.fed_tax_credits = 1
        self.prov_tax_credits = 1

    def test_cpp(self):
        paystub = self.paystub_one
        employee = self.emp
        
        CPP_MAX_CONTRIBUTION = get_cpp_max_contribution(paystub)

        self.assertEqual(CPP_MAX_CONTRIBUTION, Decimal('2163.15') )

        # Calculate the maximum contribution for this year, which for most
        # people is CPP_MAX_CONTRIBUTION, but it may be less for employees
        # turning 18 or 70 during the year
        Cmax = CPP_MAX_CONTRIBUTION * employee.cpp_elegibilty_factor()

        self.assertEqual(Cmax, Decimal('2163.15'))
        
        CPP_CONTRIBUTION_RATE = get_cpp_contribution_rate(paystub)
        
        self.assertEqual(CPP_CONTRIBUTION_RATE, Decimal('0.0495'))

        CPP_BASIC_EXEMPTION = get_cpp_basic_exemption(paystub)
        
        self.assertEqual(CPP_BASIC_EXEMPTION, Decimal('3500'))

        # this is the only case I know of where the CRA says to truncate instead
        # of rounding with next digit
        #
        # Prorate the basic exception to a per pay period amount
        CPP_BASIC_EXEMPTION_PRORATE = decimal_truncate_two_places(
            CPP_BASIC_EXEMPTION / employee.payperiods_P )    
        self.assertEqual(employee.payperiods_P, Decimal(26))
        self.assertEqual(CPP_BASIC_EXEMPTION_PRORATE, Decimal('134.61'))

        # the deduction is the cpp rate times the non-excempt income
        cpp_deduction_C = neg2zero(
            CPP_CONTRIBUTION_RATE *
            (paystub.gross_income() - CPP_BASIC_EXEMPTION_PRORATE)
            ) # neg2zero
    
        # take either the calculated deduction, or the amount of cpp required
        # to reach the maximum annual contribution, which ever is smaller
        cpp_deduction_C = min(cpp_deduction_C,
                          Cmax - employee.get_cpp_YTD(paystub) )
        
        # Round using third decimal digit, a 5 is round up
        cpp_deduction_C = decimal_round_two_place_using_third_digit(
            cpp_deduction_C)
    
        
if __name__ == '__main__':
    main()
