# provinces.py
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

from income_tax import calc_annual_basic_provincial_tax_T4
from functions import \
    neg2zero, ZERO, \
    convert_tuple_of_strings_to_tuple_of_decimals

from payroll_rule_period import \
     JUL_2006, JAN_2007, JAN_2008, JAN_2009, APR_2009, JAN_2010, JAN_2011, \
     JUL_2011, JAN_2012, \
     get_payroll_rule_period_for_paystub

from decimal import Decimal

class Province(object):
    def lowest_tax_rate(province, paystub):
        return province.get_provincial_thresholds_and_tax_rates(
            paystub)[1][0][0]
    lowest_tax_rate=classmethod(lowest_tax_rate)

    def calc_prov_surtax_V1(province, paystub):
        return ZERO
    calc_prov_surtax_V1=classmethod(calc_prov_surtax_V1)

    def calc_prov_additional_health_tax_V2(province, paystub):
        return ZERO
    calc_prov_additional_health_tax_V2 = \
        classmethod(calc_prov_additional_health_tax_V2)

    def calc_prov_tax_reduction_S(province, paystub):
        return ZERO
    calc_prov_tax_reduction_S = classmethod(calc_prov_tax_reduction_S)

    def get_provincial_claim_amount_from_code(province, paystub, prov_code):
        return province.TD_PROV[
            get_payroll_rule_period_for_paystub(paystub) ][prov_code]
    get_provincial_claim_amount_from_code = \
        classmethod(get_provincial_claim_amount_from_code)

    def get_provincial_thresholds_and_tax_rates(province, paystub):
        return province.PROVINCIAL_THRESHOLDS_AND_TAX_RATES[
            get_payroll_rule_period_for_paystub(paystub) ]
    get_provincial_thresholds_and_tax_rates = \
        classmethod( get_provincial_thresholds_and_tax_rates )

class Manitoba( Province ):
    MINIMUM_WAGE = Decimal('10.00')
    VACATION_PAY_RATE = Decimal('0.04')
    
    PROV_NAME = 'Manitoba'

    TD_PROV = { JUL_2006: ( '0.00',     # 0
                            '7734.00',  # 1
                            '8580.50',  # 2
                            '10273.50', # 3
                            '11966.50', # 4
                            '13659.50', # 5
                            '15352.50', # 6
                            '17045.50', # 7
                            '18738.50', # 8
                            '20431.50', # 9 
                            '22124.50', #10
                           ), # JUL_2006

                JAN_2007: ( '0.00',     # 0
                            '7834.00',  # 1
                            '8680.50',  # 2
                            '10373.50', # 3
                            '12066.50', # 4
                            '13759.50', # 5
                            '15452.50', # 6
                            '17145.50', # 7
                            '18838.50', # 8
                            '20531.50', # 9
                            '22224.50', # 10
                            ), # JAN_2007

                JAN_2008: ( '0.00',     # 0
                            '8034.00',  # 1
                            '8880.50',  # 2
                            '10573.50', # 3
                            '12266.50', # 4
                            '13959.50', # 5
                            '15652.50', # 6
                            '17345.50', # 7
                            '19038.50', # 8
                            '20731.50', # 9
                            '22424.50', # 10
                            ), # JAN_2008
                JAN_2009: ( '0.00',     # 0
                            '8134.00',  # 1
                            '8980.50',  # 2
                            '10673.50', # 3
                            '12366.50', # 4
                            '14059.50', # 5
                            '15752.50', # 6
                            '17445.50', # 7
                            '19138.50', # 8
                            '20831.50', # 9
                            '22524.50', # 10
                            ), # JAN_2009

                APR_2009: ( '0.00',     # 0
                            '8134.00',  # 1
                            '8980.50',  # 2
                            '10673.50', # 3
                            '12366.50', # 4
                            '14059.50', # 5
                            '15752.50', # 6
                            '17445.50', # 7
                            '19138.50', # 8
                            '20831.50', # 9
                            '22524.50', # 10
                            ), # APR_2009

                JAN_2010: ( '0.00',     # 0
                            '8134.00',  # 1
                            '8980.50',  # 2
                            '10673.50', # 3
                            '12366.50', # 4
                            '14059.50', # 5
                            '15752.50', # 6
                            '17445.50', # 7
                            '19138.50', # 8
                            '20831.50', # 9
                            '22524.50', # 10
                            ), # JAN_2010

                JAN_2011: ( '0.00',     # 0
                            '8134.00',  # 1
                            '8980.50',  # 2
                            '10673.50', # 3
                            '12366.50', # 4
                            '14059.50', # 5
                            '15752.50', # 6
                            '17445.50', # 7
                            '19138.50', # 8
                            '20831.50', # 9
                            '22524.50', # 10
                            ), # JAN_2011

                JUL_2011: ( '0.00',     # 0
                            '8634.00',  # 1
                            '9480.50',  # 2
                            '11173.50', # 3
                            '12866.50', # 4
                            '14559.50', # 5
                            '16252.50', # 6
                            '17945.50', # 7
                            '19638.50', # 8
                            '21331.50', # 9
                            '23024.50', # 10
                            ), # JUL_2011

                JAN_2012: ( '0.00',     # 0
                            '8634.00',  # 1
                            '9480.50',  # 2
                            '11173.50', # 3
                            '12866.50', # 4
                            '14559.50', # 5
                            '16252.50', # 6
                            '17945.50', # 7
                            '19638.50', # 8
                            '21331.50', # 9
                            '23024.50', # 10
                            ), # JAN_2012
               
                } # TD_PROV

    # convert the above table values from string constants to Decimal values
    # (more convienent data entry than putting Decimal around each...)
    for period, period_table in TD_PROV.iteritems():
        TD_PROV[period] = \
            convert_tuple_of_strings_to_tuple_of_decimals(period_table)

    PROVINCIAL_THRESHOLDS_AND_TAX_RATES = {
        JUL_2006: ( ('30544', '65000' ),
                    ( ('0.109', '0'),      #         A <= 30544
                      ('0.135', '794'),    # 30544 < A <= 65000
                      ('0.174', '3329'), ) # 65000 < A
                    ), # JUL_2006

        JAN_2007: ( ('30544', '65000'),
                    ( ('0.109', '0'),      #         A <= 30544
                      ('0.130', '641'),    # 30544 < A <= 65000
                      ('0.174', '3501'), ) # 65000 < A
                    ), # JAN_2007

        JAN_2008: ( ('30544', '66000'),
                    ( ('0.1090', '0'),     #         A <= 30544
                      ('0.1275', '565'),   # 30544 < A <= 66000
                      ('0.1740', '3634'), )# 66000 < A
                    ), # JAN_2008

        JAN_2009: ( ('31000', '67000'),
                    ( ('0.1080', '0'),     #         A <= 31000
                      ('0.1275', '605'),   # 31000 < A <= 67000
                      ('0.1740', '3720'), )# 67000 < A
                    ), # JAN_2009

        APR_2009: ( ('31000', '67000'),
                    ( ('0.1080', '0'),     #         A <= 31000
                      ('0.1275', '605'),   # 31000 < A <= 67000
                      ('0.1740', '3720'), )# 67000 < A
                    ), # APR_2009

        JAN_2010: ( ('31000', '67000'),
                    ( ('0.1080', '0'),     #         A <= 31000
                      ('0.1275', '605'),   # 31000 < A <= 67000
                      ('0.1740', '3720'), )# 67000 < A
                    ), # JAN_2010

        JAN_2011: ( ('31000', '67000'),
                    ( ('0.1080', '0'),     #         A <= 31000
                      ('0.1275', '605'),   # 31000 < A <= 67000
                      ('0.1740', '3720'), )# 67000 < A
                    ), # JAN_2011
                                           
        JUL_2011: ( ('31000', '67000'),
                    ( ('0.1080', '0'),     #         A <= 31000
                      ('0.1275', '605'),   # 31000 < A <= 67000
                      ('0.1740', '3720'), )# 67000 < A
                    ), # JUL_2011

        JAN_2012: ( ('31000', '67000'),
                    ( ('0.1080', '0'),     #         A <= 31000
                      ('0.1275', '605'),   # 31000 < A <= 67000
                      ('0.1740', '3720'), )# 67000 < A
                    ), # JAN_2012
        
        } # PROVINCIAL_THRESHOLDS_AND_TAX_RATES

    # convert the above table values from string constants to Decimal values
    # (more convienent data entry than putting Decimal around each...)
    for period, (thresholds, rates) in \
            PROVINCIAL_THRESHOLDS_AND_TAX_RATES.iteritems():
        # each period is a tuple, the first tuple is the thresholds,
        # the second tuple contains V,KP pairs (rate)
        PROVINCIAL_THRESHOLDS_AND_TAX_RATES[period] = (
            # thresholds
            convert_tuple_of_strings_to_tuple_of_decimals(thresholds),

            # V,KP pairs
            tuple( convert_tuple_of_strings_to_tuple_of_decimals(rate)
                   for rate in rates )
            ) # outer tuple
            
    def calc_prov_tax_reduction_S(province, paystub):
        """Note, that this is no longer used (for Manitoba) in 2008,
        2007 was the last year it returned anything. Now it returns 0.
        """
        # only calculate something if the pay period is
        # between July 2006 and the end of 2007
        if get_payroll_rule_period_for_paystub(paystub) in \
           (JUL_2006, JAN_2007):
            employee = paystub.employee

            net_annual_income_A1 = \
                paystub.projected_annual_taxable_income_A() + \
                employee.prescribed_zone_income_deduction_HD()

            annual_basic_provincial_tax_T4 = \
                calc_annual_basic_provincial_tax_T4(paystub)


            S_THRES = Decimal('225')
            S_RATE = Decimal('0.01')

            Y = province.calculate_Y(employee)
            S = neg2zero(
                min( annual_basic_provincial_tax_T4,
                     S_THRES + Y - (net_annual_income_A1*S_RATE )
                     ) ) # neg2zero( min( 
        # else, this is no longer calculated
        else:
            S = ZERO
        
        return S
    calc_prov_tax_reduction_S = classmethod(calc_prov_tax_reduction_S)

    def calculate_Y(province, employee):
        return Decimal(str(sum(employee.Y_factor_credits.itervalues() )))
    calculate_Y = classmethod(calculate_Y)

class Alberta( Province ):
    PROV_NAME='Alberta'

class British_Columbia( Province ):
    PROV_NAME='British Columbia'

class Newfoundland_and_Labrador( Province ):
    PROV_NAME='Newfoundland and Labrador'

class New_Brunswick( Province ):
    PROV_NAME='New Brunswick'

class Northwest_Territories( Province ):
    PROV_NAME='Northwest Territories'

class Nova_Scotia( Province ):
    PROV_NAME='Nova Scotia'

class Nunavut( Province ):
    PROV_NAME='Nunavut'

class Ontario( Province ):
    PROV_NAME='Ontario'

class Prince_Edward_Island( Province ):
    PROV_NAME='Price Edward Island'

class Quebec( Province ):
    PROV_NAME='Quebec'

class Saskatchewan( Province ):
    PROV_NAME='Saskatchewan'

class Yukon( Province ):
    PROV_NAME='Yukon'

class Outside( Province ):
    PROV_NAME='Outside'

# A dictionary that maps province abreviations to province class names
province_abrev = {
    'AB': Alberta,
    'BC': British_Columbia,
    'MB': Manitoba,
    'NB': New_Brunswick,
    'NL': Newfoundland_and_Labrador, 
    'NT': Northwest_Territories,
    'NS': Nova_Scotia,
    'NU': Nunavut,
    'ON': Ontario,
    'PE': Prince_Edward_Island,
    'QC': Quebec,
    'SK': Saskatchewan,
    'YT': Yukon,
    'OC': Outside
    }

# set RESIDES in every province class to be the province abreviation
for (abrev, prov_class) in province_abrev.iteritems():
    prov_class.RESIDES = abrev


# A tuple of all the province abreviations, sorted and with OC (Outside) at
# the back
province_list = province_abrev.keys()
province_list.sort()
province_list.remove('OC')
province_list.append('OC')
province_list = tuple(province_list)

province_choices_temp = [(prov, prov.lower(), province_abrev[prov].PROV_NAME )
                         for prov in province_list ]

# a tuple of all the ways of representing the provinces, upper and lower case
# abreviations and the province's name, eg '(AB, ab, Alberta, BC, ...
province_choices = []
for prov in province_choices_temp:
    province_choices.extend(prov)
province_choices = tuple(province_choices)


# extend province_abrev to contain a mapping for all of the lower case
# abreviations and the full province names to the province classes
for province_class in province_abrev.values():
    # map lower case abrev
    province_abrev[ province_class.RESIDES.lower() ] = province_class
    # map full name
    province_abrev[province_class.PROV_NAME ] = province_class 



# Add support for unofficial province and teritory names and abreviations
unofficial_abrev = {
    Alberta: ('Alta', 'alta', 'Alta.', 'alta.'),
    British_Columbia: ('B.C.', 'b.c.', 'C.-B.', 'c.-b.' ),
    Manitoba: ( 'Man', 'man', 'Man.', 'man.' ),
    New_Brunswick: ('N.B.', 'n.b.'),
    Newfoundland_and_Labrador: ('NF', 'nf', 'Newfoundland',
                                         'Nfld.', 'Nfld', 'nfld', 'nfld.' ),
    Northwest_Territories: ('N.W.T.', 'n.w.t.', 'NWT', 'nwt'),
    Nova_Scotia: ('N.S.', 'n.s.', 'N.-E', 'n.-e'),
    Ontario: ('Ont', 'ont', 'Ont.', 'ont.'),
    Prince_Edward_Island: ('PEI', 'pie', 'P.E.I.', 'p.e.i.'),
    Quebec: ('Que.', 'Que', 'que.', 'que', 'P.Q.', 'p.q.',
                      'PQ', 'pq', 'QU', 'qu'),
    Saskatchewan: ('Sask.', 'Sask', 'sask.', 'sask'),
    Yukon: ('Yuk.', 'yuk.', 'Yuk', 'yuk', 'YK', 'yk'),
    Outside: ('OT', 'ot')
    }
for (province_class, name_list) in unofficial_abrev.iteritems():
    for prov in name_list:
        province_abrev[prov] = province_class

