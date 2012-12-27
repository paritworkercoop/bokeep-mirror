# income_tax.py
# Copyright (C) 2006-2011 ParIT Worker Co-operative <paritinfo@parit.ca>
# Copyright (C) 2001-2007 Paul Evans <pevans@catholic.org>
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
#            Paul Evans <pevans@catholic.org>
#            Samuel Pauls <samuel@parit.ca>

from paystub_line import \
     PaystubCalculatedDeductionLine, PaystubDeductionLine, \
     PaystubSimpleDeductionLine
     
from cpp import get_cpp_max_contribution
from ei import get_max_ei_premium
from functions import neg2zero, range_table_lookup, ZERO, \
    convert_tuple_of_strings_to_tuple_of_decimals, \
    convert_dict_of_string_to_dict_of_decimals_in_place, \
    decimal_round_two_place_using_third_digit

from decimal import Decimal

from itertools import imap

from payroll_rule_period import \
     JUL_2006, JAN_2007, JAN_2008, JAN_2009, APR_2009, JAN_2010, JAN_2011, \
     JUL_2011, JAN_2012, JAN_2013, \
     get_payroll_rule_period_for_paystub


FEDERAL_CLAIM_CODE_TABLE = { JUL_2006: [ '0.00',     # 0
                                         '8639.00',  # 1
                                         '9562.50',  # 2
                                         '11409.50', # 3
                                         '13256.50', # 4
                                         '15103.50', # 5
                                         '16950.50', # 6
                                         '18797.50', # 7
                                         '20644.50', # 8
                                         '22491.50', # 9
                                         '24338.50'  # 10
                                         ],
                             
                             JAN_2007: [ '0.00',     # 0
                                         '8929.00',  # 1
                                         '9873.00',  # 2
                                         '11761.00', # 3
                                         '13649.00', # 4
                                         '15537.00', # 5
                                         '17425.00', # 6
                                         '19313.00', # 7
                                         '21201.00', # 8
                                         '23089.00', # 9
                                         '24977.00', # 10
                                         ],
                             JAN_2008: [ '0.00',     # 0
                                         '9600.00',  # 1
                                         '10562.00',  # 2
                                         '12486.00', # 3
                                         '14410.00', # 4
                                         '16334.00', # 5
                                         '18258.00', # 6
                                         '20182.00', # 7
                                         '22106.00', # 8
                                         '24030.00', # 9
                                         '25954.00', # 10
                                         ],
                             JAN_2009: [ '0.00',     # 0 
                                         '10100.00',  # 1
                                         '11086.00',  # 2 
                                         '13058.00', # 3 
                                         '15030.00', # 4 
                                         '17002.00', # 5 
                                         '18974.00', # 6 
                                         '20946.00', # 7 
                                         '22918.00', # 8 
                                         '24890.00', # 9 
                                         '26862.00', # 10 
                                         ],
                             APR_2009: [ '0.00',     # 0 
                                         '10375.00', # 1
                                         '11361.00', # 2 
                                         '13333.00', # 3 
                                         '15305.00', # 4 
                                         '17277.00', # 5 
                                         '19249.00', # 6 
                                         '21221.00', # 7 
                                         '23193.00', # 8 
                                         '25165.00', # 9 
                                         '27137.00', # 10 
                                         ],

                             JAN_2010: [ '0.00',     # 0
                                         '10382.00', # 1
                                         '11374.00', # 2 
                                         '13358.00', # 3 
                                         '15342.00', # 4 
                                         '17326.00', # 5 
                                         '19310.00', # 6 
                                         '21294.00', # 7 
                                         '23278.00', # 8 
                                         '25262.00', # 9 
                                         '27246.00', # 10 
                                         ],

                             JAN_2011: [ '0.00',     # 0
                                         '10527.00', # 1
                                         '11532.50', # 2 
                                         '13543.50', # 3 
                                         '15554.50', # 4 
                                         '17565.50', # 5 
                                         '19576.50', # 6 
                                         '21587.50', # 7 
                                         '23598.50', # 8 
                                         '25609.50', # 9 
                                         '27620.50', # 10 
                                         ],
                            
                             JUL_2011: [ '0.00',     # 0
                                         '10527.00', # 1
                                         '11532.50', # 2 
                                         '13543.50', # 3 
                                         '15554.50', # 4 
                                         '17565.50', # 5 
                                         '19576.50', # 6 
                                         '21587.50', # 7 
                                         '23598.50', # 8 
                                         '25609.50', # 9 
                                         '27620.50', # 10 
                                         ],
                             
                             JAN_2012: [ '0.00',     # 0
                                         '10822.00', # 1
                                         '11856.00', # 2 
                                         '13924.00', # 3 
                                         '15992.00', # 4 
                                         '18060.00', # 5 
                                         '20128.00', # 6 
                                         '22196.00', # 7 
                                         '24264.00', # 8 
                                         '26332.00', # 9 
                                         '28400.00', # 10 
                                         ],

                             JAN_2013: [ '0.00',     # 0
                                         '11038.00', # 1
                                         '12092.50', # 2 
                                         '14201.50', # 3 
                                         '16310.50', # 4 
                                         '18419.50', # 5 
                                         '20528.50', # 6 
                                         '22637.50', # 7 
                                         '24756.50', # 8 
                                         '26855.50', # 9 
                                         '28964.50', # 10 
                                         ],
                             }
# convert the above table values from string constants to Decimal values
# (more convienent data entry than putting Decimal around each...)
for period, period_table in FEDERAL_CLAIM_CODE_TABLE.iteritems():
    FEDERAL_CLAIM_CODE_TABLE[period] = \
        convert_tuple_of_strings_to_tuple_of_decimals(period_table)

FEDERAL_TAX_RATES_AND_THRESHOLDS = {
    JUL_2006: ( ('36378', '72756', '118285'),
                ( ('0.155', '0'),   #          A <= 36378
                  ('0.22', '2365'), # 36378  < A <= 72756
                  ('0.26', '5275'), # 72756  < A <= 118285
                  ('0.29', '8823'), # 118285 < A
                  ) ), # JUL_2006
    
    JAN_2007: ( ('37178', '74357', '120887'),
                ( ('0.155', '0'),   #          A <= 37178
                  ('0.22', '2417'), # 37178  < A <= 74357
                  ('0.26', '5391'), # 74357  < A <= 120887
                  ('0.29', '9017'), # 120887 < A
                  ) ), # JAN_2007

    JAN_2008: ( ('37885', '75769', '123184'),
                ( ('0.15', '0'),    #          A <= 37885
                  ('0.22', '2652'), # 37885  < A <= 75769
                  ('0.26', '5683'), # 75769  < A <= 123184
                  ('0.29', '9378'), # 123184 < A
                  ) ), # JAN_2008
    
    JAN_2009: ( ('38832', '77664', '126264'),
                ( ('0.15', '0'),    #          A <= 38832
                  ('0.22', '2718'), # 38832  < A <= 77664
                  ('0.26', '5825'), # 77664  < A <= 126264
                  ('0.29', '9613'), # 126264 < A
                  ) ), # JAN_2009

    APR_2009: ( ('41200', '82399', '126264'),
                ( ('0.15', '0'),    #          A <= 41200
                  ('0.22', '2884'), # 41200  < A <= 82399
                  ('0.26', '6180'), # 82399  < A <= 126264
                  ('0.29', '9968'), # 126264 < A
                  ) ), # APR_2009
    JAN_2010: ( ('40970', '81941', '127021'),
                ( ('0.15', '0'),    #          A <= 40970
                  ('0.22', '2868'), # 40970  < A <= 81941
                  ('0.26', '6146'), # 81941  < A <= 127021
                  ('0.29', '9956'), # 127021 < A
                  ) ), # JAN_2010
    JAN_2011: ( ('41544', '83088', '128800'),
                ( ('0.15', '0'),    #          A <= 41544
                  ('0.22', '2908'), # 40970  < A <= 83088
                  ('0.26', '6232'), # 81941  < A <= 128800
                  ('0.29', '10096'), # 128800 < A
                  ) ), # JAN_2011
    JUL_2011: ( ('41544', '83088', '128800'),
                ( ('0.15', '0'),    #          A <= 41544
                  ('0.22', '2908'), # 40970  < A <= 83088
                  ('0.26', '6232'), # 81941  < A <= 128800
                  ('0.29', '10096'), # 128800 < A
                  ) ), # JUL_2011
    JAN_2012: ( ('42707', '85414', '132406'),
                ( ('0.15', '0'),    #          A <= 42707
                  ('0.22', '2989'), # 42707  < A <= 85414
                  ('0.26', '6406'), # 85414  < A <= 132406
                  ('0.29', '10378'), # 132406 < A
                  ) ), # JAN_2012
    JAN_2013:( ('43561', '87123', '135054'),
                ( ('0.15', '0'),    #          A <= 42707
                  ('0.22', '3049'), # 42707  < A <= 85414
                  ('0.26', '6534'), # 85414  < A <= 132406
                  ('0.29', '10586'), # 132406 < A
                  ) ), # JAN_2013

    } # FEDERAL_TAX_RATES_AND_THRESHOLDS

# convert the above table values from string constants to Decimal values
# (more convienent data entry than putting Decimal around each...)
for period, (thresholds, rates) in \
        FEDERAL_TAX_RATES_AND_THRESHOLDS.iteritems():
    # each period is a tuple, the first tuple is the thresholds,
    # the second tuple contains V,KP pairs (rate)
    FEDERAL_TAX_RATES_AND_THRESHOLDS[period] = (
        # thresholds
        convert_tuple_of_strings_to_tuple_of_decimals(thresholds),
        
        # R,K pairs
        tuple(  convert_tuple_of_strings_to_tuple_of_decimals(rate)
               for rate in rates )
        ) # outer tuple

CANADA_EMPLOYMENT_CREDIT_TABLE = { JUL_2006: '500',
                                   JAN_2007: '1000',
                                   JAN_2008: '1019',
                                   JAN_2009: '1044',
                                   APR_2009: '1044',
                                   JAN_2010: '1051',
                                   JAN_2011: '1065',
                                   JUL_2011: '1065',
                                   JAN_2012: '1095',
                                   JAN_2013: '1117',
                                   } # CANADA_EMPLOYMENT_CREDIT
convert_dict_of_string_to_dict_of_decimals_in_place(
    CANADA_EMPLOYMENT_CREDIT_TABLE)

def get_federal_claim_amount_from_code(paystub, code):
    return FEDERAL_CLAIM_CODE_TABLE[
        get_payroll_rule_period_for_paystub(paystub) ] [code]

def get_federal_thresholds_and_tax_rates(paystub):
    return FEDERAL_TAX_RATES_AND_THRESHOLDS[
        get_payroll_rule_period_for_paystub(paystub) ]
    
def get_lowest_fed_tax_rate(paystub):
    return get_federal_thresholds_and_tax_rates(paystub)[1][0][0]

def get_canada_employement_credit(paystub):
    return CANADA_EMPLOYMENT_CREDIT_TABLE[
        get_payroll_rule_period_for_paystub(paystub) ]


class PaystubIncomeTaxDeductionLine(PaystubDeductionLine):
    """Represents an income tax deduction of federal and provincial income tax

    This is an abstract class, what you really want is the subclasses
    PaystubExtraIncomeTaxDeductionLine and
    PaystubCalculatedIncomeTaxDeductionLine
    """
    
    def get_federal_part(self):
        """Get the part of this deduction that is federal income tax
        """
        raise Exception()
    def get_federal_part_(self):
        return self.get_federal_part()
    federal_part = property(get_federal_part_)

    def get_provincial_part(self):
        """Get the part of this deduction this is provincial income tax
        """
        raise Exception()
    def get_provincial_part_(self):
        return self.get_provincial_part()
    provincial_part = property(get_provincial_part_)

class PaystubExtraIncomeTaxDeductionLine(PaystubSimpleDeductionLine,
                                         PaystubIncomeTaxDeductionLine):
    def get_federal_part(self):
        """Get the part of this deduction that is federal income tax
        """
        return self.get_value()

    def get_provincial_part(self):
        """Get the part of this deduction this is provincial income tax
        """
        return 0

class PaystubCalculatedIncomeTaxDeductionLine(PaystubCalculatedDeductionLine,
                                              PaystubIncomeTaxDeductionLine):
    description = 'Income Tax Deduction'
    
    def get_calculated_value(self):
        return calculate_income_tax_deduction_T(self.paystub)

    def get_component(self, component_function):
        T, federal_ratio = calculate_income_tax_deduction_T_and_ratio(
            self.paystub)
        return component_function(T, federal_ratio)

    def get_federal_part(self):
        """Get the part of this deduction that is federal income tax
        """
        return self.get_component(calc_federal_part)

    def get_provincial_part(self):
        """Get the part of this deduction this is provincial income tax
        """
        return self.get_component(calc_provincial_part)


def calc_federal_part(T, federal_ratio):
    fp = T*federal_ratio
    fp = decimal_round_two_place_using_third_digit(fp)
    return fp

def calc_provincial_part(T, federal_ratio):
    pp = T - calc_federal_part(T, federal_ratio)
    return pp

def calculate_income_tax_deduction_T_and_ratio(paystub):
    T1 = calc_annual_fed_income_tax_T1(paystub)
    T2 = calc_annual_provincial_income_tax_T2(paystub)

    annual_income_tax = T1+T2
    T = annual_income_tax / paystub.employee.payperiods_P
    T = decimal_round_two_place_using_third_digit(T)

    if T == ZERO:
        federal_ratio = ZERO
    else:
        federal_ratio = T1/annual_income_tax

    return (T, federal_ratio)

def calculate_income_tax_deduction_T(paystub):
    T, federal_ratio = calculate_income_tax_deduction_T_and_ratio(paystub)
    return T

def calc_annual_basic_federal_income_tax_T3(paystub):
    annual_taxable_income_A = paystub.projected_annual_taxable_income_A()
    
    thresholds, R_K_table = get_federal_thresholds_and_tax_rates(paystub)

    R, K = range_table_lookup(thresholds, R_K_table, annual_taxable_income_A)

    T3 = neg2zero ( (R * annual_taxable_income_A) -
                    K -
                    projected_annual_fed_tax_reduction(paystub) )

    return T3

def calc_annual_fed_income_tax_T1(paystub):
    T3 = calc_annual_basic_federal_income_tax_T3(paystub)
    T1 = neg2zero(T3 - paystub.employee.labour_credit_fed_LCF())
    return T1

def projected_annual_fed_tax_reduction(paystub):
    """A projection of the annual income tax reduction the employee
    associated with a paystub will recieve. This comes from various
    tax credits.
    """
    # Call all the federal income tax credit functions, passing them the
    # paystub, and sum the result of calling each function
    return sum( function(paystub)
                for function in 
                ( calc_fed_non_refund_tax_credit_K1,
                  calc_fed_CPP_tax_credit_K2c,
                  calc_fed_EI_tax_credit_K2e,
                  calc_other_fed_tax_credits_K3,
                  calc_canada_employment_credit_K4, ) )

def calc_fed_non_refund_tax_credit_K1(paystub):
    """Calculates federal non-refundable tax credits
    """
    fed_tax_credits = paystub.employee.fed_tax_credits

    # If using a claim code, lookup value of the claim
    if type(fed_tax_credits) == int:
        TC = get_federal_claim_amount_from_code( paystub, fed_tax_credits )
    # Else the claim value is the sum of declared tax credits
    else:
        TC = sum(fed_tax_credits.itervalues())

    K1 = get_lowest_fed_tax_rate(paystub)*TC
    return K1


def calc_fed_CPP_tax_credit_K2c(paystub):
    """Calculates the tax credit for CPP contributions
    """
    K2c = get_lowest_fed_tax_rate(paystub) * \
        min( paystub.employee.payperiods_P * paystub.cpp_deductions(),
             get_cpp_max_contribution(paystub) )
    return K2c
    
def calc_fed_EI_tax_credit_K2e(paystub):
    """Calculates the tax credit for EI contributions
    """
    K2e = get_lowest_fed_tax_rate(paystub) * \
        min( paystub.employee.payperiods_P * paystub.ei_deductions(),
             get_max_ei_premium(paystub) )
    return K2e

def calc_other_fed_tax_credits_K3(paystub):
    """Calculates the value of 'other' federal tax credits, examples include
    medical expenses and charitble donations. These are always authorized by
    a tax centre.
    """
    K3 = sum( paystub.employee.other_fed_tax_credits.itervalues() )
    return K3

def calc_canada_employment_credit_K4(paystub):
    """Calculates the projected value of the canada employment tax credit.
    """
    annual_taxable_income_A = paystub.projected_annual_taxable_income_A()
    lowest_fed_tax_rate = get_lowest_fed_tax_rate(paystub)
    K4 = min( lowest_fed_tax_rate * annual_taxable_income_A,
              lowest_fed_tax_rate * get_canada_employement_credit(paystub) )
    return K4


def calc_annual_basic_provincial_tax_T4(paystub):
    province = paystub.employee.province
    annual_taxable_income_A = paystub.projected_annual_taxable_income_A()

    thresholds, V_KP_table = province.get_provincial_thresholds_and_tax_rates(
        paystub)

    V, KP = range_table_lookup( thresholds, V_KP_table,
                                annual_taxable_income_A )
    T4 = (V * annual_taxable_income_A) - KP - \
         projected_annual_prov_tax_reduction(paystub)
    return T4

def calc_annual_provincial_income_tax_T2(paystub):
    employee = paystub.employee
    province = employee.province
    
    annual_basic_provincial_tax_T4 = \
        calc_annual_basic_provincial_tax_T4(paystub)
        
    T2 = neg2zero(
        annual_basic_provincial_tax_T4 + \
        province.calc_prov_surtax_V1(paystub) + \
        province.calc_prov_additional_health_tax_V2(paystub) - \
        province.calc_prov_tax_reduction_S(paystub) - \
        employee.labour_credit_prov_LCP() )
    return T2


def calc_prov_non_refund_tax_credit_K1P(paystub):
    # Only validated to work with Manitoba so far...
    employee = paystub.employee
    province = employee.province
    prov_tax_credits = employee.prov_tax_credits
    
    # If using a claim code, lookup value of the claim 
    if type(prov_tax_credits) == int:
        TCP = province.get_provincial_claim_amount_from_code(
            paystub, prov_tax_credits )
    # Else the claim value is the sum of declared tax credits
    else:
        TCP = sum(prov_tax_credits.itervalues())
    K1P = province.lowest_tax_rate(paystub) * TCP

    return K1P

def calc_prov_CPP_tax_credit_K2Pc(paystub):
    # Only validated to work with Manitoba so far...
    employee = paystub.employee
    K2Pc = employee.province.lowest_tax_rate(paystub) * \
        min( employee.payperiods_P * paystub.cpp_deductions(),
             get_cpp_max_contribution(paystub) )
    return K2Pc

def calc_prov_EI_tax_credit_K2Pe(paystub):
    # Only validated to work with Manitoba so far...
    employee = paystub.employee
    K2Pe = employee.province.lowest_tax_rate(paystub) * \
           min( employee.payperiods_P * paystub.ei_deductions(),
                get_max_ei_premium(paystub) )
    return K2Pe

def calc_other_prov_tax_credits_K3P(paystub):
    K3P = sum( paystub.employee.other_prov_tax_credits.itervalues() )
    return K3P

def projected_annual_prov_tax_reduction(paystub):
    return sum( function(paystub)
                for function in 
                ( calc_prov_non_refund_tax_credit_K1P,
                  calc_prov_CPP_tax_credit_K2Pc,
                  calc_prov_EI_tax_credit_K2Pe,
                  calc_other_prov_tax_credits_K3P ) )
