# cpp.py CPP deductions calculations for Canada
# Copyright (C) 2001-2006 Paul Evans <pevans@catholic.org>
# Copyright (C) 2006-2014 ParIT Worker Co-operative <paritinfo@parit.ca>
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

from functions import neg2zero, \
    convert_dict_of_string_to_dict_of_decimals_in_place, \
    decimal_round_two_place_using_third_digit, \
    decimal_truncate_two_places
    
from decimal import Decimal

from payroll_rule_period import \
     JUL_2006, JAN_2007, JAN_2008, JAN_2009, APR_2009, JAN_2010, JAN_2011, \
     JUL_2011, JAN_2012, JAN_2013, JAN_2014, \
     get_payroll_rule_period_for_paystub


CPP_CONTRIBUTION_RATE_TABLE = { JUL_2006: '0.0495', # 4.95%
                                JAN_2007: '0.0495', # 4.95%
                                JAN_2008: '0.0495', # 4.95%
                                JAN_2009: '0.0495', # 4.95%
                                APR_2009: '0.0495', # 4.95%
                                JAN_2010: '0.0495', # 4.95%
                                JAN_2011: '0.0495', # 4.95%
                                JUL_2011: '0.0495', # 4.95%
                                JAN_2012: '0.0495', # 4.95%
                                JAN_2013: '0.0495', # 4.95%
                                JAN_2014: '0.0495', # 4.95%
                                }
convert_dict_of_string_to_dict_of_decimals_in_place(CPP_CONTRIBUTION_RATE_TABLE)

CPP_MAX_CONTRIBUTION_TABLE = { JUL_2006: '1910.70',
                               JAN_2007: '1989.90',
                               JAN_2008: '2049.30',
                               JAN_2009: '2118.60',
                               APR_2009: '2118.60',
                               JAN_2010: '2163.15',
                               JAN_2011: '2217.60',
                               JUL_2011: '2217.60',
                               JAN_2012: '2306.70',
                               JAN_2013: '2356.20',
                               JAN_2014: '2425.50',
                               }
convert_dict_of_string_to_dict_of_decimals_in_place(CPP_MAX_CONTRIBUTION_TABLE)

CPP_BASIC_EXEMPTION_TABLE = { JUL_2006: '3500.00',
                              JAN_2007: '3500.00',
                              JAN_2008: '3500.00',
                              JAN_2009: '3500.00',
                              APR_2009: '3500.00',
                              JAN_2010: '3500.00',
                              JAN_2011: '3500.00',
                              JUL_2011: '3500.00',
                              JAN_2012: '3500.00',
                              JAN_2013: '3500.00',
                              JAN_2014: '3500.00',
                              }
convert_dict_of_string_to_dict_of_decimals_in_place(CPP_BASIC_EXEMPTION_TABLE)

def get_cpp_contribution_rate(paystub):
    return CPP_CONTRIBUTION_RATE_TABLE[
        get_payroll_rule_period_for_paystub(paystub) ]

def get_cpp_max_contribution(paystub):
    return CPP_MAX_CONTRIBUTION_TABLE[
        get_payroll_rule_period_for_paystub(paystub) ]

def get_cpp_basic_exemption(paystub):
    return CPP_BASIC_EXEMPTION_TABLE[
        get_payroll_rule_period_for_paystub(paystub) ]

def calculate_cpp_deduction(paystub):
    employee = paystub.employee

    CPP_MAX_CONTRIBUTION = get_cpp_max_contribution(paystub)

    # Calculate the maximum contribution for this year, which for most
    # people is CPP_MAX_CONTRIBUTION, but it may be less for employees
    # turning 18 or 70 during the year
    Cmax = CPP_MAX_CONTRIBUTION * employee.cpp_elegibilty_factor()

    CPP_CONTRIBUTION_RATE = get_cpp_contribution_rate(paystub)

    CPP_BASIC_EXEMPTION = get_cpp_basic_exemption(paystub)

    # this is the only case I know of where the CRA says to truncate instead
    # of rounding with next digit
    #
    # Prorate the basic exception to a per pay period amount
    CPP_BASIC_EXEMPTION_PRORATE = decimal_truncate_two_places(
        CPP_BASIC_EXEMPTION / employee.payperiods_P )    

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
    
    return cpp_deduction_C

    

class PaystubCPPDeductionLine(PaystubCalculatedDeductionLine):
    """Represents a CPP deduction
    """
    description = 'CPP Deduction'

    def get_calculated_value(self):
        return calculate_cpp_deduction(self.paystub)

class PaystubCPPEmployerContributionLine(
    PaystubCalculatedEmployerContributionLine):
    """A contribution by an Employer to cpp
    """
    description = 'Employer CPP Contribution'

    def get_calculated_value(self):
        return calculate_cpp_deduction(self.paystub)


