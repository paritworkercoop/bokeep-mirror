# vacation_pay.py CPP deductions calculations for Canada
# Copyright (C) 2006-2010 ParIT Worker Co-operative <paritinfo@parit.ca>
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
#            Mark Jenkins <mark@parit.ca>

from functions import ZERO, decimal_round_two_place_using_third_digit
from paystub_line import PaystubCalculatedLine, PaystubIncomeLine, \
    sum_paystub_lines

from decimal import Decimal

class VacationPayoutTooMuchException(Exception):
    pass

class PaystubVacationPayAvailable(PaystubCalculatedLine):
    def get_calculated_value(self):
        all_time_vacpay = \
            self.paystub.employee.get_sum_of_all_paystub_line_class(
            PaystubVacpayLine, self.paystub, True)
        
        all_time_vacpayouts = \
            self.paystub.employee.get_sum_of_all_paystub_line_class(
            PaystubVacpayPayoutLine, self.paystub, True)
        
        vacpay_available = all_time_vacpay - all_time_vacpayouts
        vacpay_available = decimal_round_two_place_using_third_digit(
            vacpay_available)
        return vacpay_available

    def get_net_value(self):
        # Zero because a status report on vacation pay has no effect on net pay
        return ZERO

class PaystubVacpayLine(PaystubCalculatedLine):
    """A PaystubLine for vacation pay.  It's important to note that this line
       does NOT represent income until it's claimed, and thus cannot be a
       PaystubIncomeLine.
    """
    description = 'vacation pay'

    def get_calculated_value(self):
        # you earn vacation pay on earned income, not on vacation pay
        # being paid out, else you'd become very rich
      
        vacpay = self.paystub.employee.vacation_rate * \
            sum( (paystub_line.get_value()
                  for paystub_line in \
                      self.paystub.get_paystub_lines_of_classes_not_classes(
                    (PaystubIncomeLine,), (PaystubVacpayPayoutLine,) )
                  ), # end generator expression
                 ZERO )
        vacpay = decimal_round_two_place_using_third_digit(vacpay)
        return vacpay
            

    def get_net_value(self):
        # Zero because vacation pay no effect on net pay
        return ZERO

class PaystubVacpayPayoutLine(PaystubCalculatedLine, PaystubIncomeLine):
    """Income earned by taking accrued vacation pay.

    Only one PaystubVacPayPayoutLine should appear per paystub per payperiod,
    because having more than one is not compatible with the current
    implementation of get_caculated_value and set_value which assume only
    one.

    Note to Jamie who thought more than one should be an option:
    Really, how should a calculated PaystubVacpayPayoutLine be
    calculated if there is another PaystubVacpayPayoutLine present in the same
    paystub? If they're both calculated, you get mutual recursion. Even if they
    avoid that, two calculated PaystubVacpayPayoutLines (using the current
    calculation algorithm) will be two much together. If one is
    mannually set and the other is calculated, you need something new in the
    api to say this calculated one uses the manualy set one or code it to
    say that the calculated PaystubVacpayoutLine should not consider the other
    but not itself...

    For now, get_calculated_value does consider accrued vacpay from the
    current paystub, but not any VacpayPayout's from the same paystub
    (a reasonable assumption assuming we stick to only having one)
    """
    description = 'vacation pay, pay out'

    def __init__(self, paystub, value=None):
        PaystubCalculatedLine.__init__(self, paystub)
        if value != None:
            self.set_value(value)

    def get_calculated_value(self):
        """Calculated to be the most vacation pay that can be removed,
        including greedilly taking the vacation pay earned this period.

        The greedy aproach of taking vacation pay earned this period
        is what people want when they take thier vacation pay out in the
        same period where they earn income.

        This doesn't cause a problem for people
        who take thier vacation pay in periods
        where they don't work at all, because no new vacation pay is accured
        (see PaystubVacpayLine.get_calculated_value) when there is not any
        non-vacation pay income.

        This greedy aproach may not be prefered for employes who work a small
        amount during the pay period where they take thier vacation pay but
        would only like to be paid out for vacation pay earned in the
        previous pay periods. For those, cases, you can override the
        calculated value with the value returned by
        get_non_greedy_value()
        """
        ytd_vacpay = \
            self.paystub.employee.get_sum_of_all_paystub_line_class(
            PaystubVacpayLine, self.paystub, True)

        ytd_vacpayouts = \
            self.paystub.employee.get_sum_of_all_paystub_line_class(
            PaystubVacpayPayoutLine, self.paystub, False)

        vacpayout = ytd_vacpay - ytd_vacpayouts
        vacpayout = decimal_round_two_place_using_third_digit(
            vacpayout)
        return vacpayout
        
    def set_value(self, value):
        # don't allow vacation payouts to be larger than the calculated
        # maximum vacation payout value
        if value > self.get_calculated_value():
            raise VacationPayoutTooMuchException()
        PaystubCalculatedLine.set_value(self, value)
    
    def get_non_greedy_value(self):
        # simply subtract the greedyness from get_calculated_value
        non_greed = self.get_calculated_value() - \
            sum_paystub_lines(
            self.paystub.get_paystub_lines_of_class(PaystubVacpayPayoutLine)
            )
        non_greed = decimal_round_two_place_using_third_digit(
            non_greed)
        return non_greed
