# paystub_line.py 
# Copyright (C) 2006 ParIT Worker Co-operative <paritinfo@parit.ca>
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
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
# Author(s): Mark Jenkins <mark@parit.ca>


from itertools import ifilter, ifilterfalse, imap
from decimal import Decimal
from functions import decimal_round_two_place_using_third_digit, ZERO

# zopedb
from persistent import Persistent

def sum_paystub_lines_with_function(paystub_lines, paystub_access_function):
    """Sum a list/iterable of paystub lines by adding the result of calling
    paystub_access_function on each paystub
    """
    lwf = sum(
        (paystub_access_function(line) for line in paystub_lines),
        ZERO )

    # is this even necessary...?
    lwf = decimal_round_two_place_using_third_digit(lwf)
    return lwf

def sum_paystub_lines(paystub_lines):
    """Sum the result of calling get_value() on a list/interable of
    paystub lines
    """
    def get_paystub_line_value(paystub_line):
        return paystub_line.get_value()
    return sum_paystub_lines_with_function(paystub_lines,
                                           get_paystub_line_value)

def sum_paystub_lines_for_net_pay(paystub_lines):
    """Sum the result of caling get_net_value on a list/iterable of
    paystub lines
    """
    def get_paystub_line_net_value(paystub_line):
        return paystub_line.get_net_value()
    return sum_paystub_lines_with_function(paystub_lines,
                                           get_paystub_line_net_value )

def get_paystub_line_taxable(paystub_line):
    return paystub_line.get_taxable()

def filter_for_tax_exempt_lines(paystub_lines):
    return ifilterfalse(get_paystub_line_taxable,
                        paystub_lines )

def filter_for_taxable_lines(paystub_lines):
    return ifilter(get_paystub_line_taxable,
                   paystub_lines)

class PaystubLine(Persistent):
    """A line on a paystub.

    This could be something such as hours and a wage,
    a bonus, a deduction, a deducted advance, a union due,
    a payout of holiday pay, an employer contribution to a employement
    insurance or a pension plan...

    Attributes:

    description -- Text describing the item

    taxable -- True if this paystub line represents taxable income, or
    a deduction from taxable income. The property tax_exempt is availible
    to always hold the opposite value.
    False examples: deductions for contributions to RRSPs, union dues, and
    alimony payments
    True examples: wages, advances, employee contributions to equity in a
    worker co-operative
    """
    description = ''
    taxable = True

    def __init__(self, paystub, *args, **kargs):
        self.paystub = paystub
        if len(args)>0 or len(kargs)>0:
            self.set_value(*args, **kargs)

    def get_value(self):
        """The value of the line, always a positive number
        """

        return self.__value

    def set_value(self, value):
        self.__value = value
    
    def get_net_value(self):
        """The net effect this line has on the pay. Income lines should
        be positive here, employee deductions should be negative, and employer
        contributions should be zero.
        """
        return self.get_value()

    def get_taxable(self):
        return self.taxable

    def get_value_components(self):
        return (self.get_value(),)

    def __str__(self):
        return self.description + ': ' + str(self.get_value())
  

class PaystubIncomeLine(PaystubLine):
    """A PaystubLine that represents some form of income
    """
    description = 'income'

class PaystubWageLine(PaystubIncomeLine):
    """A PaystubLine for income made by the hour.

    Attributes:
    rate -- The rate of pay for the hours worked
    hours -- The number of hours worked
    These can also be set through set_value(rate, hours)
    """

    description = 'wages'
    
    def __init__(self, paystub, hours=0, rate=None):
        if rate==None:
            rate = paystub.employee.default_rate
        PaystubIncomeLine.__init__(self, paystub, hours, rate)
    
    def set_value(self, hours, rate):
        self.hours = hours
        self.rate = rate

    def get_unrounded_value(self):
        return self.hours * self.rate

    def get_value(self):
        return decimal_round_two_place_using_third_digit(
            self.get_unrounded_value() )

    def get_value_components(self):
        return (self.hours, self.rate)
    

class PaystubOvertimeWageLine(PaystubWageLine):
    """A PaystubWageLine with overtime.

    Attributes:
    overtime_multiplier -- A multiplier to increase the rate of pay for
    overtime wages.
    """

    description = 'overtime wages'
    
    def set_value(self, hours, rate, overtime_multiplier):
        PaystubWageLine.set_value(rate, hours)
        self.overtime_multiplier = overtime_multiplier

    def get_value(self):
        return decimal_round_two_place_using_third_digit(
    PaystubWageLine.get_unrounded_value(self)*self.overtime_multiplier )

    def get_value_components(self):
        components = list(PaystubWageLine.get_value_components(self))
        components.append(self.overtime_multiplier)
        return tuple(components)

class PaystubCalculatedLine(PaystubLine):
    """Subclasses must define get_calculated_value
    """
    override = False

    # We override PaystubLine.__init__ to make it explicit that
    # the paystub is the only argument of interest for calculated lines
    def __init__(self, paystub):
        PaystubLine.__init__(self, paystub)
    
    def get_value(self):
        if self.override:
            return PaystubLine.get_value(self)
        else:
            return self.get_calculated_value()

    def set_value(self, value):
        PaystubLine.set_value(self, value)
        self.override = True

    def freeze_value(self):
        self.set_value(self.get_value())

    def recalculate_value(self):
        self.override = False
        return self.get_value()

class PaystubSummaryLine(PaystubCalculatedLine):
    def get_net_value(self):
        return ZERO

class PaystubNetPaySummaryLine(PaystubSummaryLine):
    def get_calculated_value(self):
        return self.paystub.net_pay()

class PaystubTotalIncomeLine(PaystubSummaryLine):
    def get_calculated_value(self):
        return self.paystub.gross_pay()

class PaystubDeductionLine(PaystubLine):
    """A line that represents a deduction from the net pay.
    """
    def get_net_value(self):
        # Note the negation, deductions have a negative effect on net pay.
        return - self.get_value()

class PaystubMultipleOfIncomeLine(PaystubCalculatedLine):
    constant = Decimal(1)

    def get_calculated_value(self):
        return decimal_round_two_place_using_third_digit(
    self.constant * self.paystub.gross_income() )
    
class PaystubDeductionMultipleOfIncomeLine(PaystubMultipleOfIncomeLine,
                                           PaystubDeductionLine):
    pass

class PaystubSimpleDeductionLine(PaystubDeductionLine):
    def __init__(self, paystub, amount=0.0):
        PaystubLine.__init__(self, paystub, amount)
        
class PaystubCalculatedDeductionLine(PaystubCalculatedLine,
                                     PaystubDeductionLine):
    # Because of the multiple inheritance, we have to override this
    # function. Putting PaystubDeductionLine first would screw up
    # get_value() and set_value(), putting PaystubCalculatedLine first
    # screws up get_net_value().
    #
    # Any new methods that get added to PaystubDeductionLine that are 
    # also implemented by PaystubCalculatedLine or its super class(es)
    # Will need to be redefined here too.
    #
    # The nice thing is I didn't find this out the hard way, which is how
    # most people get wacked by multiple inheritance. I read the fucking
    # manual, and learnt about python's depth first left to right
    # resolution rule.
    #
    # So, why even leave PaystubDeduction line there? So we can say
    # that an instance of PaystubCalculatedDeductionLine is an instance of
    # both classes.
    get_net_value = PaystubDeductionLine.get_net_value


class PaystubEmployerContributionLine(PaystubLine):
    """A paystub line that represents a contribution by an employer
    """
    # By default employer contributions don't have tax implications for the
    # employee
    taxable = False
    
    def get_net_value(self):
        # Zero because employer contributions have no effect on net pay
        return ZERO

class PaystubCalculatedEmployerContributionLine(
    PaystubCalculatedLine, PaystubEmployerContributionLine):

    # Look at the comment for get_net_value in PaystubCalculatedDeductionLine
    # Read it and think very carefully about the implications on
    # this class, which is very similar
    get_net_value = PaystubEmployerContributionLine.get_net_value

class PaystubEmployerContributionMultipleOfIncomeLine(
    PaystubMultipleOfIncomeLine,
    PaystubEmployerContributionLine):
    pass
