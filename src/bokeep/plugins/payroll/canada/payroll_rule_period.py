# payroll_rule_period.py 
# Copyright (C) 2006-2008 ParIT Worker Co-operative <paritinfo@parit.ca>
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

JUL_2006, JAN_2007, JAN_2008, JAN_2009, APR_2009, JAN_2010 = range(6)
LAST_RULE_PERIOD = JAN_2010

CODE_TO_YEAR_AND_MONTHS = { JUL_2006: (2006, range(7, 12+1) ),
                            JAN_2007: (2007, range(1, 12+1) ),
                            JAN_2008: (2008, range(1, 12+1) ),
                            JAN_2009: (2009, range(1, 3+1) ),
                            APR_2009: (2009, range(4, 12+1) ),
                            JAN_2010: (2010, range(1, 12+1) ),

                            }

YEAR_AND_MONTH_TO_CODE = {}

for rule_period_code, (year, months) in CODE_TO_YEAR_AND_MONTHS.iteritems():
    for month in months:
        YEAR_AND_MONTH_TO_CODE[ (year, month) ] = rule_period_code
        
def get_payroll_rule_period_from_date(paydate):
    try:
        return_value = YEAR_AND_MONTH_TO_CODE[ (paydate.year,
                                                paydate.month) ]
    except KeyError:
        return_value = LAST_RULE_PERIOD

    return return_value

def get_payroll_rule_period_for_paystub(paystub):
    return get_payroll_rule_period_from_date(paystub.payday.paydate)
