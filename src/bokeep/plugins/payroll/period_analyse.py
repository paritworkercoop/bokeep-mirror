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
# Author: Mark Jenkins <mark@parit.ca>

# python imports
from sys import stdout
from decimal import Decimal
from datetime import date, timedelta
from bisect import bisect_right
import csv

# a dictionary with a period name as key, and number of months in that
# kind of period as the value
PERIODS = {"monthly": 1,
           "quarterly": 3,
           "yearly": 12 }

NUM_MONTHS = 12

ONE_DAY = timedelta(days=1)

ZERO = Decimal(0)


def next_period_start(start_year, start_month, period_type):
    # add numbers of months for the period length
    end_month = start_month + PERIODS[period_type]
    # use integer division to find out if the new end month is in a different
    # year, what year it is, and what the end month number should be changed
    # to.
    # Because this depends on modular arithmatic, we have to curvert the month
    # values from 1-12 to 0-11 by subtracting 1 and putting it back after
    #
    # the really cool part is that this whole thing is implemented without
    # any branching; if end_month > NUM_MONTHS
    #
    # A the super nice thing is that you can add all kinds of period lengths
    # to PERIODS
    end_year = start_year + ( (end_month-1) / NUM_MONTHS )
    end_month = ( (end_month-1) % NUM_MONTHS ) + 1

    return end_year, end_month
    

def period_end(start_year, start_month, period_type):
    if period_type not in PERIODS:
        raise Exception("%s is not a valid period, should be %s" % (
                period_type, str(PERIODS.keys()) ) )

    end_year, end_month = next_period_start(start_year, start_month,
                                            period_type)

    # last step, the end date is day back from the start of the next period
    # so we get a period end like
    # 2010-03-31 for period starting 2010-01 instead of 2010-04-01
    return date(end_year, end_month, 1) - ONE_DAY
    

def generate_period_boundaries(
    start_year, start_month, period_type, periods):
    for i in xrange(periods):
        yield ( date(start_year, start_month, 1),
                period_end(start_year, start_month, period_type) )
        start_year, start_month = next_period_start(
            start_year, start_month, period_type)

def period_analyse(payroll_mod, start_year, start_month,
                   periods, period_type, output_file_path):
    start_year, start_month, periods = (
        int(blah)
        for blah in (start_year, start_month, periods) )

    # a list of all the periods of interest, for each period
    # keep the start date, end date, and ei, cpp, and income tax sums
    period_list = [
        [start_date, end_date,
         ZERO, # employee ei deductions
         ZERO, # employer ei contributions
         ZERO, # employee cpp deductions
         ZERO, # employer cpp contributions
         ZERO, # employee income tax deductions
         ZERO, # employee gross pay
         ]
        for start_date, end_date in generate_period_boundaries(
            start_year, start_month, period_type, periods)
        ]
    # a copy of the above list with just the period start dates
    period_starts = [e[0] for e in period_list ]
    
    for payday in payroll_mod.get_paydays().itervalues():
        paydate = payday.paydate

        # use binary search to find the period that starts before or on
        # the transaction date
        period_index = bisect_right( period_starts, paydate ) - 1

        # ignore paydays with a date before the matching period start
        # (after subtracting 1 above start_index would be -1)
        # and after the last period_end
        if period_index >= 0 and \
                paydate <= period_list[len(period_list)-1][1]:

            # get the period bucket appropriate for the split in question
            period = period_list[period_index]

            # more specifically, we'd expect the transaction date
            # to be on or after the period start, and  before or on the
            # period end, assuming the binary search (bisect_right)
            # assumptions from above are are right..
            #
            # in other words, we assert our use of binary search
            # and the filtered results from the above if provide all the
            # protection we need
            assert( paydate>= period[0] and paydate <= period[1] )

            for paystub in payday.paystubs:
                for i, deduction_or_contribution in enumerate((
                    paystub.ei_deductions(),
                    paystub.employer_ei_contributions(),
                    paystub.cpp_deductions(),
                    paystub.employer_cpp_contributions(),
                    paystub.income_tax_deductions(),
                    paystub.gross_income() )):

                    period[2+i] += Decimal("%.2f" % deduction_or_contribution )

    output_file = file(output_file_path, 'w')
    csv_writer = csv.writer(output_file)
    csv_writer.writerow(
        ('period start', 'period end',
         'employee ei deductions', 'employer ei contributions', 'total ei',
         'employee cpp deductions', 'employer cpp contributions', 'total cpp',
         'employee income tax deductions',
         'total deductions and contributions',
         'gross income') )
    csv_writer.writerows(
        (start_date, end_date,
         employee_ei, employer_ei, employee_ei + employer_ei,
         employee_cpp, employer_cpp, employee_cpp + employer_cpp,
         employee_income_tax,
         employee_ei + employer_ei + employee_cpp + employer_cpp +
         employee_income_tax, gross_income, 
         )
        for start_date, end_date, employee_ei, employer_ei, \
            employee_cpp, employer_cpp, employee_income_tax, gross_income \
            in period_list
        )
    output_file.close()

