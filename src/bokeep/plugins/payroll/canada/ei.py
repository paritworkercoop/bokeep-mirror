# ei.py EI payroll deductions calculations for Canada
# Copyright (C) 2001-2006 Paul Evans <pevans@catholic.org>
# Copyright (C) 2006-2011 ParIT Worker Co-operative <paritinfo@parit.ca>
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
# Author(s): Paul Evans <pevans@catholic.org>
#            Mark Jenkins <mark@parit.ca>
#            Samuel Pauls <samuel@parit.ca>

from paystub_line import \
     PaystubCalculatedDeductionLine, PaystubCalculatedEmployerContributionLine

from payroll_rule_period import \
     JUL_2006, JAN_2007, JAN_2008, JAN_2009, APR_2009, JAN_2010, JAN_2011, \
     JUL_2011, JAN_2012, JAN_2013, JAN_2014, JAN_2015, JAN_2016, \
     get_payroll_rule_period_for_paystub

from functions import decimal_round_two_place_using_third_digit, \
    convert_dict_of_string_to_dict_of_decimals_in_place

from decimal import Decimal

# EI constants

# employer contributes 1.4 times what employee does
EMPLOYER_EI_RATE = Decimal('1.4') 

EI_RATE_TABLE = { JUL_2006: '0.0187', # 1.87%
                  JAN_2007: '0.018',  # 1.8%
                  JAN_2008: '0.0173', # 1.73%
                  JAN_2009: '0.0173', # 1.73%
                  APR_2009: '0.0173', # 1.73%
                  JAN_2010: '0.0173', # 1.73%
                  JAN_2011: '0.0178', # 1.73%
                  JUL_2011: '0.0178', # 1.78%
                  JAN_2012: '0.0183', # 1.83%
                  JAN_2013: '0.0188', # 1.88%
                  JAN_2014: '0.0188', # 1.88%
                  JAN_2015: '0.0188', # 1.88%
                  JAN_2016: '0.0188', # 1.88%
                  }
convert_dict_of_string_to_dict_of_decimals_in_place(EI_RATE_TABLE)

MAX_EI_PREMIUM_TABLE = { JUL_2006: '729.30',
                         JAN_2007: '720.00',
                         JAN_2008: '711.03',
                         JAN_2009: '731.79',
                         APR_2009: '731.79',
                         JAN_2010: '747.36',
                         JAN_2011: '786.76',
                         JUL_2011: '786.76',
                         JAN_2012: '839.97',
                         JAN_2013: '891.12',
                         JAN_2014: '913.68',
                         JAN_2015: '930.60',
                         JAN_2016: '955.04',
                         }
convert_dict_of_string_to_dict_of_decimals_in_place(MAX_EI_PREMIUM_TABLE)

def get_ei_rate(paystub):
    return EI_RATE_TABLE[ get_payroll_rule_period_for_paystub(paystub) ]

def get_max_ei_premium(paystub):
    return MAX_EI_PREMIUM_TABLE[ get_payroll_rule_period_for_paystub(paystub) ]

def calculate_ei_deduction(paystub):
    ei_rate = get_ei_rate(paystub)
    max_ei_premium = get_max_ei_premium(paystub)

    # use either a calculated EI premium or the amount of primium required
    # to get up to the annual maximum, whichever is smaller
    EI = min( ei_rate * paystub.gross_income(),
              max_ei_premium - paystub.employee.get_ei_YTD(paystub) )

    # Round using third decimal digit, a 5 is round up
    EI = decimal_round_two_place_using_third_digit(EI)

    return EI
    

class PaystubEIDeductionLine(PaystubCalculatedDeductionLine):
    """Represents a CPP deduction
    """
    description = 'EI Deduction'

    def get_calculated_value(self):
        return calculate_ei_deduction(self.paystub)

class PaystubEIEmployerContributionLine(
    PaystubCalculatedEmployerContributionLine):
    """A contribution by an Employer to cpp
    """
    description = 'Employer EI Contribution'

    def get_calculated_value(self):
        EIemp = calculate_ei_deduction(self.paystub) * EMPLOYER_EI_RATE

        #set to two decimal places
        EIemp = decimal_round_two_place_using_third_digit(EIemp)

        return EIemp

EI_RATE_QUEBEC = Decimal('0.0141') # 1.41%
MAX_EI_PREMIUM_QUEBEC = Decimal('623.22')
    
