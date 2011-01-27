# Copyright (C) 2010  ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
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
# Author: Mark Jenkins <mark@parit.ca>

# python imports
from datetime import date
from unittest import TestCase, main
from decimal import Decimal

# cdnpayroll imports
from bokeep.plugins.payroll.canada.employee import Employee
from bokeep.plugins.payroll.payroll import Payday
from bokeep.plugins.payroll.canada.paystub import Paystub
from bokeep.plugins.payroll.canada.paystub_line import PaystubIncomeLine, sum_paystub_lines, \
    PaystubCalculatedLine
from bokeep.plugins.payroll.canada.vacation_pay import \
    PaystubVacpayLine, PaystubVacpayPayoutLine, \
    VacationPayoutTooMuchException, PaystubVacationPayAvailable
from bokeep.plugins.payroll.canada.functions import ZERO

class BasicVacationPayTest(TestCase):
    def setUp(self):
        self.emp = Employee("test employee")
        date_paydate_one = date(2009, 01, 01)
        self.payday_one = Payday(None)
        self.payday_one.set_paydate(
            *(date_paydate_one for i in xrange(3)) )
        self.paystub_one = Paystub(self.emp, self.payday_one)
        self.paystub_one.add_paystub_line(
            PaystubIncomeLine( self.paystub_one, Decimal(100) ) )
        self.paystub_one_vacpaylines = tuple(
            self.paystub_one.get_paystub_lines_of_class(PaystubVacpayLine))
        self.paystub_one_vacpayline = self.paystub_one_vacpaylines[0]
        self.paystub_one_vacpayavail = PaystubVacationPayAvailable(
            self.paystub_one)
        self.paystub_one.add_paystub_line(self.paystub_one_vacpayavail)

class TestVacationPay(BasicVacationPayTest):
    def test_vac_pay_rate(self):
        self.assertEqual( self.emp.vacation_rate, Decimal('0.04') )

    def test_one_vac_pay_line(self):
        self.assertEqual( len(self.paystub_one_vacpaylines), 1)

    def test_vac_pay_amount(self):
        self.assertEqual( self.paystub_one_vacpayline.get_value(), Decimal(4) )
        self.assert_(
            self.paystub_one_vacpayline.get_value().as_tuple()[2] >= -2 )

class TestBadVacationPayoutCreate(BasicVacationPayTest):
    def setUp(self):
        BasicVacationPayTest.setUp(self)
        self.paystub_one_vacpayout =  PaystubVacpayPayoutLine(self.paystub_one)
        # an intentional mistake is made here, failing to add the
        # new paystub line to the paystub

    def test_get_paystub_lines_of_class(self):
        vacpayouts = tuple( 
            self.paystub_one.get_paystub_lines_of_class(
                PaystubVacpayPayoutLine) )
        # this would be 1 if the itentional mistake in api usage wasn't made
        self.assertEqual( len(vacpayouts), 0)
    
class BasicVacationPayout(BasicVacationPayTest):
    def setUp(self):
        BasicVacationPayTest.setUp(self)
        self.paystub_one_vacpayout =  PaystubVacpayPayoutLine(self.paystub_one)
        # don't make the intentional mistake that was made in
        # TestBadVacationPayoutCreate
        self.paystub_one.add_paystub_line(self.paystub_one_vacpayout)

class TestVacationPayout(BasicVacationPayout):
    def test_sum_function_on_payout(self):
        self.assertEqual(
            Decimal(4),
            self.paystub_one.employee.get_sum_of_all_paystub_line_class(
                PaystubVacpayPayoutLine, self.paystub_one, True) )

        self.assertEqual(
            ZERO,
            self.paystub_one.employee.get_sum_of_all_paystub_line_class(
                PaystubVacpayPayoutLine, self.paystub_one, False ) )

    def test_get_all_paystub_lines_PaystubVacpayPayoutLine(self):
        all_payout_lines = tuple(
            self.paystub_one.employee.get_all_paystub_lines_of_class(
                PaystubVacpayPayoutLine,
                self.paystub_one,
                True ) )

        self.assertEqual(1, len(all_payout_lines) )

        all_payout_lines = tuple(
            self.emp.get_all_paystub_lines_of_class(
                PaystubVacpayPayoutLine,
                self.paystub_one,
                True ) )

        self.assertEqual( 1, len(all_payout_lines) )

    def test_get_all_paystubs(self):
        all_paystubs_not_including_current = tuple(
            self.emp.get_all_paystubs(self.paystub_one, False) )
        self.assertEqual(len(all_paystubs_not_including_current), 0)

        all_paystubs_including_current = tuple(
            self.emp.get_all_paystubs(self.paystub_one, True) )
        self.assertEqual(len(all_paystubs_including_current), 1)
    
        self.assertEqual( all_paystubs_including_current[0],
                          self.paystub_one )

    def test_get_paystub_lines_of_class(self):
        vacpayouts = tuple( 
            self.paystub_one.get_paystub_lines_of_class(
                PaystubVacpayPayoutLine) )
        self.assertEqual( len(vacpayouts), 1)


    def test_vacation_payout_matches_vacation_pay(self):
        self.assertEqual( self.paystub_one_vacpayout.get_value(),
                          self.paystub_one_vacpayline.get_value() )

        self.assertEqual( self.paystub_one_vacpayout.get_value(),
                          Decimal(4) )

        self.assertEqual( self.paystub_one_vacpayline.get_value(), Decimal(4) )


    def test_vacation_payout_matches_vacation_pay_with_freeze(self):        
        self.paystub_one_vacpayout.freeze_value()
        self.assertEqual( self.paystub_one_vacpayout.get_value(),
                          self.paystub_one_vacpayline.get_value() )

        self.assertEqual( self.paystub_one_vacpayout.get_value(),
                          Decimal(4) )

        self.assertEqual( self.paystub_one_vacpayline.get_value(), Decimal(4) )

    def test_vacation_payout_reasonable_override(self):
        self.paystub_one_vacpayout.set_value( Decimal(3) )
        self.assertEqual( self.paystub_one_vacpayout.get_value(),
                          Decimal(3) )
        self.assertEqual( self.paystub_one_vacpayout.get_calculated_value(),
                          Decimal(4) )

        self.assertEquals(self.paystub_one_vacpayavail.get_value(),
                          Decimal(1) )

    def test_vacation_payout_reasonable_override_match(self):
        self.paystub_one_vacpayout.set_value( Decimal(4) )
        self.assertEqual( self.paystub_one_vacpayout.get_value(),
                          Decimal(4) )
        self.assertEqual( self.paystub_one_vacpayout.get_calculated_value(),
                          Decimal(4) )

    def test_vacation_payout_bad_override(self):
        self.assertRaises( VacationPayoutTooMuchException,
            self.paystub_one_vacpayout.set_value, Decimal(5) )

    def test_vacation_payout_trickster_override(self):
        PaystubCalculatedLine.set_value( self.paystub_one_vacpayout,
                                         Decimal(4) )
        self.assertRaises( VacationPayoutTooMuchException,
            self.paystub_one_vacpayout.set_value, Decimal(5) )        


class TestFixedVacationPayOut(BasicVacationPayTest):
    def setUp(self):
        BasicVacationPayTest.setUp(self)
        self.paystub_one_vacpayout =  PaystubVacpayPayoutLine(
            self.paystub_one, Decimal(3))
        # don't make the intentional mistake that was made in
        # TestBadVacationPayoutCreate
        self.paystub_one.add_paystub_line(self.paystub_one_vacpayout)
    
    def test_vacation_payout_available_with_fixed(self):
        self.assertEquals(self.paystub_one_vacpayavail.get_value(),
                          Decimal(1) )

class ComplexVacationPayout(BasicVacationPayout):
    def setUp(self):
        BasicVacationPayout.setUp(self)
        
        date_paydate_two = date(2009, 01, 15)
        self.payday_two = Payday(None)
        self.payday_two.set_paydate(
            *(date_paydate_two for i in xrange(3)) )
        self.paystub_two = Paystub(self.emp, self.payday_two)
        self.paystub_two.add_paystub_line(
            PaystubIncomeLine( self.paystub_two, Decimal(200) ) )
        # payday two does not contain a vacation pay widthdrawel line

        date_paydate_three = date(2009, 01, 29)
        self.payday_three = Payday(None)
        self.payday_three.set_paydate(
            *(date_paydate_three for i in xrange(3)) )
        self.paystub_three = Paystub(self.emp, self.payday_three)
        self.paystub_three.add_paystub_line(
            PaystubIncomeLine( self.paystub_three, Decimal(100) ) )
        self.paystub_three_vacpayout = PaystubVacpayPayoutLine(
            self.paystub_three) 
        self.paystub_three.add_paystub_line(self.paystub_three_vacpayout)


        date_paydate_four = date(2009, 02, 13)
        self.payday_four = Payday(None)
        self.payday_four.set_paydate(
            *(date_paydate_four for i in xrange(3)) )
        self.paystub_four = Paystub(self.emp, self.payday_four)
        self.paystub_four.add_paystub_line(
            PaystubIncomeLine( self.paystub_four, Decimal(100) ) )
        self.paystub_four_vacpayout = PaystubVacpayPayoutLine(
            self.paystub_four)
        self.paystub_four.add_paystub_line( self.paystub_four_vacpayout )
        

    def test_vacpayout_two_value(self):
        self.assertEqual(
            sum_paystub_lines( self.paystub_two.get_paystub_lines_of_class(
                    PaystubVacpayPayoutLine)) ,
            Decimal(0) )

    def test_vacpayout_three_value(self):
        self.assertEqual( self.paystub_three_vacpayout.get_value(),
                          Decimal(12) )

    def test_vacpayout_four_value(self):
        self.assertEqual( self.paystub_four_vacpayout.get_value(),
                          Decimal(4) )

    def test_change_vacpayout_three_to_zero(self):
        self.paystub_three_vacpayout.set_value(Decimal(0))
        self.assertEqual( self.paystub_three_vacpayout.get_value(),
                          Decimal(0) )
        self.assertEqual( self.paystub_four_vacpayout.get_value(),
                          Decimal(16) )
    
    def test_change_vacpaytout_three_to_bad(self):
        self.assertRaises( VacationPayoutTooMuchException,
                           self.paystub_three_vacpayout.set_value,
                           Decimal(13) )

    def test_change_vacpayout_three_to_something_modest(self):
        self.paystub_three_vacpayout.set_value(Decimal(6))
        self.assertEqual(self.paystub_three_vacpayout.get_value(),
                         Decimal(6) )
        self.assertEqual(self.paystub_four_vacpayout.get_value(),
                         Decimal(10) )

    def test_change_vacpayout_four_to_something_modest(self):
        self.paystub_four_vacpayout.set_value(Decimal(2))
        self.assertEqual(self.paystub_three_vacpayout.get_value(),
                         Decimal(12) )
        self.assertEqual(self.paystub_four_vacpayout.get_value(),
                         Decimal(2) )

    def test_change_vacpayout_three_after_freezing_four(self):
        self.paystub_four_vacpayout.freeze_value()
        self.assertEqual( self.paystub_three_vacpayout.get_value(),
                          Decimal(12) )
        self.assertEqual( self.paystub_four_vacpayout.get_value(),
                          Decimal(4) )

if __name__ == '__main__':
    main()
