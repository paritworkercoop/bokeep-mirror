# employee.py
# Copyright (C) 2006 ParIT Worker Co-operative <paritinfo@parit.ca>
# Copyright (C) 2001-2006 Paul Evans <pevans@catholic.org>
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

from persistent.list import PersistentList

from cpp import PaystubCPPDeductionLine, PaystubCPPEmployerContributionLine
from ei import PaystubEIDeductionLine, PaystubEIEmployerContributionLine
from income_tax import PaystubCalculatedIncomeTaxDeductionLine
from vacation_pay import PaystubVacpayLine
from timesheet import Timesheet

from provinces import Manitoba
from paystub import Paystub
from paystub_line import PaystubWageLine, sum_paystub_lines
from functions import iterate_until_value, ZERO, \
    convert_dict_of_string_to_dict_of_decimals_in_place, \
    decimal_round_two_place_using_third_digit
from bokeep.util import start_of_year
from decimal import Decimal
from datetime import date, MINYEAR, MAXYEAR

# zopedb
from persistent import Persistent

# one of the posible keys for Employee.annual_income_deductions
LIVING_IN_A_PRESCRIBED_ZONE='living in a prescribed zone'

BASIC_PERSONAL_AMOUNT = 'basic personal amount'

# Number of months in a year
MONTHS_PER_YEAR = Decimal(12)

WEEKS_PER_YEAR = Decimal(52)

tax_credits = {
    BASIC_PERSONAL_AMOUNT: '10527.00',
    'child amount': '2131.00',
    'age amount': '6537.00',
    'pension income amount': '2000.00',
    'amount for a month of full-time education' : '465.00',
    'amount for a month of part-time education' : '140.00',
    'disability amount': '7341.00',
    'spouse or common-law partner amount': '10527.00',
    'amount for an eligible dependant': '10527.00',
    'caregiver amount': '4282.00',
    'amount for an infirm dependant age 18 or older': '4282.00'
    }
# convient to use strings instead of Decimal('xxxx.xx') above
convert_dict_of_string_to_dict_of_decimals_in_place(tax_credits)

# Constants to describe the number of pay periods per year
MONTHLY = MONTHS_PER_YEAR
SEMI_MONTHLY = MONTHS_PER_YEAR * Decimal(2)
BI_WEEKLY = WEEKS_PER_YEAR / Decimal(2) # Could also be 27
WEEKLY = WEEKS_PER_YEAR # Could also be 53 

# a dictionary that maps the number of pay periods in a year to the
# word used to describe that pay cycle
pay_periods_map = {
MONTHLY : 'monthly',
SEMI_MONTHLY : 'semi-monthly',
BI_WEEKLY : 'bi-weekly',
WEEKLY : 'weekly'
}


FED_LABOUR_SPONSORED_TAX_CREDIT_PERCENT  = Decimal('0.15') # 15%
PROV_LABOUR_SPONSORED_TAX_CREDIT_PERCENT = Decimal('0.15') # 15%

START_OF_PERIOD, END_OF_PERIOD = range(2)

NO_ROE_END_DATE = None

class Employee(Persistent):
    """An employee is a person remunerated via payroll.

    Atributes:

    paystubs -- A list of Paystubs associated with this employee

    calcuated_paystub_line_functions -- A list of functions that are called
    to create new paystub lines. Each function is passed a paystub,
    and returns one or more PaystubLines.
    
    annual_income_deductions -- A dict representing annual deductions, such
    as the deduction for living in a prescribed zone (HD), or other
    deductions (F1). The key is a description, the value is the value of
    the annual deduction. (A positive number). The function 
    sum_annual_income_deductions provides the sum of these values

    fed_tax_credits -- A dict representing federal tax credits this employee
    is elegible for. Example tax credits: The basic personal amount, the age
    amount, the pension income amount, the caregiver amount, the full time
    education amount... The keys are descriptions of the tax credits,
    the values are the actual values of the tax credit. As an alternative,
    you can make fed_tax_credits an integer which represents a claim code,
    these claim codes co-respond to tax credit claim ammounts in a table.
    You can lookup claim codes in payroll guides.

    prov_tax_credits -- Like fed_tax_credits, only for provincial ones.

    other_fed_tax_credits -- A dict representing 'other' federal tax credits,
    that are applying differently then the ones in fed_tax_credits. The data
    structure is the same, a dict with a descriptive key and a value
    representing the value of the tax credit. These are different from
    fed_tax_credits in how they're applyed, the credits from fed_tax_credits
    are multiplied by the lowest tax rate when they are deducted from income,
    these ones are just deducted directly. They're labeled K3 in the payroll
    calculations.

    other_prov_tax_credits -- Like other_fed_tax_credits, only for provincial
    ones.


    The ROE work term functions, init_roe_work_periods, start_roe_work_period,
    end_roe_work_period, current_roe_work_period_available,
    get_current_roe_work_period_start, get_latest_roe_work_period,
    roe_work_period_exists, get_num_roe_work_periods, get_all_roe_work_periods,
    get_paystubs_for_roe_work_period, help you define work periods for
    ROE generation purposes.

    New employees created by instantiating new Employee objects will already
    have the required data strcutures, but old Employee ojbects from prior
    version of cdnpayroll will not. For each of these you should call
    init_roe_work_periods once.

    When a new employee starts working, you'll probably want to call
    start_roe_work_period() right away to log when they started, you may
    want to pair this with your code that creates the new Employee() object.

    For old Employee objects from prior versions of cdnpayroll,
    you should look up when they started, and call this funtion for them to
    define when they started as well. If there are any old Employees from old
    versions of cdnpayroll who ended thier employment, you should call
    end_roe_work_period() after calling start_work_period() so both the start
    and end date are in the system. For old employees who have been back and
    forth, call start_work_period() and end_roe_work_period(), back and forth
    as many times as required, ending with start_work_period() or
    end_roe_work_period() depending on wether they are now currently working.

    When the employement of a employee ends in the future, you should call
    end_roe_work_period() before trying to generate an ROE.

    To generate an ROE, you identify the period you'd like the ROE to cover
    by using get_latest_roe_work_period() [for the simple case of the period
    just ended], get_all_roe_work_periods(), or roe_work_period_exists().
    You can retrive all the paystubs for that period by using
    get_paystubs_for_roe_work_period()
    
    """
    
    # The number of months per year this employee will contribute to CPP
    # Is 12 for most people, but may be less for someone turning 18 this year
    # (who doesn't contribute until they are 18), or someone turning 70
    cpp_months = MONTHS_PER_YEAR

    LCFin = LCPin = ZERO

    # The number of pay periods for this employee during the year
    payperiods_P = BI_WEEKLY

    province = Manitoba

    auto_add_lines = [
        PaystubCPPDeductionLine,
        PaystubCPPEmployerContributionLine,
        PaystubEIDeductionLine,
        PaystubEIEmployerContributionLine,
        PaystubCalculatedIncomeTaxDeductionLine,
        PaystubVacpayLine,
        ]

    def __init__(self, name=None):
        self.paystubs = []
        self.__init_timesheets()
        self.archived_paystubs = None
        self.auto_add_lines = list(self.auto_add_lines)

        self.name = name

        self.annual_income_deductions = {}

        self.fed_tax_credits = 1
        self.prov_tax_credits = 1

        self.other_fed_tax_credits = {}
        self.other_prov_tax_credits = {}

        self.Y_factor_credits = {}

        self.default_rate = self.province.MINIMUM_WAGE

        self.init_roe_work_periods()
        self._p_changed = True

    def get_rate(self):
        if hasattr(self, 'rate'):
            return self.rate 
        else:
            return self.default_rate

    def add_paystub(self, paystub):
        self.paystubs.append(paystub)
        self._p_changed = True

    def __init_timesheets(self):
        # earlier versions didn't have the timesheets array, add if needed
        if not hasattr(self, 'timesheets'):
            self.timesheets = PersistentList()

    def add_timesheet(self, date, hours, memo):
        sheet = Timesheet(date, hours, memo)
        self.__init_timesheets()

        self.timesheets.append(sheet)


    #for 'record of employment' info, cap the most date if desired
    def get_last_timesheet(self, maxdate=None):
        last_sheet = None
        for timesheet in self.timesheets:
            if (last_sheet == None or timesheet.sheet_date > last_sheet.sheet_date) and (maxdate == None or timesheet.sheet_date <= maxdate):
                last_sheet = timesheet

        return last_sheet

    def get_timesheets(self, start_date=date(MINYEAR, 1, 1),
                       end_date=date(MAXYEAR, 12, 31)):
        self.__init_timesheets()

        if (start_date.year == MINYEAR) and (end_date.year == MAXYEAR):
            return self.timesheets

        sheets_to_return = []
        for timesheet in self.timesheets:
            if timesheet.sheet_date >= start_date and \
                    timesheet.sheet_date <= end_date:
                sheets_to_return.append(timesheet)

        return sheets_to_return
        
    def drop_timesheets(self, start_date=date(MINYEAR, 1, 1),
                        end_date=date(MAXYEAR, 12, 31)):
        self.__init_timesheets()

        if (start_date.year == MINYEAR) and (end_date.year == MAXYEAR):
            self.timesheets = []

        sheets_to_keep = []
 
        for timesheet in self.timesheets:
            if timesheet.sheet_date < start_date or \
                    timesheet.sheet_date > end_date:
                sheets_to_keep.append(timesheet)

        self.timesheets = sheets_to_keep
        


    def create_and_add_new_paystub(self, payday):
        return Paystub(self, payday)

    def cpp_elegibilty_factor(self):
        return self.cpp_months / MONTHS_PER_YEAR

    def sum_annual_income_deductions(self):
        """The sum of annual_income_deductions. See the comment for
        annual_income_deductions in the class description
        """
        return sum( self.annual_income_deductions.itervalues() )

    def prescribed_zone_income_deduction_HD(self):
        if self.annual_income_deductions.has_key(LIVING_IN_A_PRESCRIBED_ZONE):
            return annual_income_deductions[LIVING_IN_A_PRESCRIBED_ZONE]
        else:
            return ZERO

    def get_all_paystub_lines_of_class(self, paystub_line_class,
                                       stop_at_paystub,
                                       include_final_paystub=False):
        """Get all the paystub lines from this year that are members of
        paystub_line_calss
        """
        for paystub in self.get_all_paystubs(
            stop_at_paystub, include_final_paystub):
            for paystub_line in \
                paystub.get_paystub_lines_of_class(paystub_line_class):
                yield paystub_line

    def get_bounded_paystub_lines_of_class(self, paystub_line_class,
                                           startdate, enddate,
                                           stop_at_paystub=None,
                                           include_final_paystub=True):
        """Get all the paystub lines in the given time window that are members 
        of paystub_line_calss
        """
        for paystub in self.get_bounded_paystubs(startdate, enddate,
                                                 stop_at_paystub,
                                                 include_final_paystub):
            for paystub_line in \
                    paystub.get_paystub_lines_of_class(paystub_line_class):
                yield paystub_line

    def get_bounded_paystubs(self, startdate, enddate,
                             stop_at_paystub=None,
                             include_final_paystub=True):
        for paystub in self.paystubs:
            if paystub.payday.paydate >= startdate and \
                    paystub.payday.paydate <= enddate:
                # if we've reached the final paystub, and if we're not
                # including it, stop
                if paystub == stop_at_paystub and \
                        not include_final_paystub:
                    break
                # current paystub
                yield paystub
                # stop if we just yielded the last one
                if paystub == stop_at_paystub:
                    break
                

    def get_all_paystubs(self, stop_at_paystub, include_final_paystub=False):
        """Provides a generator that gives access to all paystubs associated
        with this employee, except for
        ones listed in the argument except (which is a tuple or list)
        """
        return iterate_until_value(self.paystubs, stop_at_paystub,
                                   include_final_paystub)

    def get_sum_of_all_paystub_line_class(self, paystub_line_class,
                                          stop_at_paystub,
                                          include_final_paystub=False):
        return sum_paystub_lines(
            self.get_all_paystub_lines_of_class(paystub_line_class,
                                                stop_at_paystub,
                                                include_final_paystub) )

    def get_YTD_sum_of_paystub_line_class(self, paystub_line_class,
                                          stop_at_paystub,
                                          include_final_paystub=False):
        last_date  = stop_at_paystub.payday.paydate
        return self.get_bounded_sum_of_paystub_line_class(
            paystub_line_class,
            start_of_year(stop_at_paystub.payday.paydate), last_date,
            stop_at_paystub, include_final_paystub)

    def get_bounded_sum_of_paystub_line_class(self, paystub_line_class,
                                              startdate, enddate,
                                              stop_at_paystub=None,
                                              include_final_paystub=True):
        return sum_paystub_lines(
            self.get_bounded_paystub_lines_of_class(
                    paystub_line_class,
                    startdate, enddate,
                    stop_at_paystub,
                    include_final_paystub) )
                

    def get_cpp_YTD(self, stop_at_paystub):
        return self.get_YTD_sum_of_paystub_line_class(
           PaystubCPPDeductionLine, stop_at_paystub)

    def get_ei_YTD(self, stop_at_paystub ):
        return self.get_YTD_sum_of_paystub_line_class(
           PaystubEIDeductionLine, stop_at_paystub)

    def labour_credit_fed_LCF(self):
        lcfl = min(self.LCFin * FED_LABOUR_SPONSORED_TAX_CREDIT_PERCENT,
                   Decimal(750))
        lcfl = decimal_round_two_place_using_third_digit(lcfl)

        return lcfl
    

    def labour_credit_prov_LCP(self):
        # This needs province specific implementation...
        return 0

    def __str__(self):
        retstr = 'name: ' + self.name + '\n'
        if hasattr(self, 'rate'):
            retstr += 'rate: ' + str(self.rate) + '\n'
        else:
            retstr += 'default rate: ' + str(self.default_rate) + '\n'

        self.__init_timesheets()

        if len(self.timesheets) > 0:
            retstr += 'vvvvTimesheetsvvvv\n'
            for timesheet in self.timesheets:
                retstr += str(timesheet)
            retstr += '^^^^Timesheets^^^^\n'
        return retstr

    def __repr__(self):
        return self.__str__()

    def init_roe_work_periods(self):
        """Initialize the list of work periods for ROE purposes
        Only works if the list doesn't exist yet, otherwise it exceptions
        """
        # a list of tuples, each element represents a work period
        # for ROE purposes
        #
        # The first element of each tuple is a start date
        # the second element of each tuple is and end date
        # to represent a period that hasn't yet ended,

        if hasattr(self, '_Employee__roe_work_periods'):
            raise RoeWorkPeriodsAlreadyInit()
        else:
            self.__roe_work_periods = []
        self._p_changed = True

    def start_roe_work_period(self, start_date):
        """Designate that a work period (for ROE purposes) has begun.

        The argument start_date must be of type datetime.date
        You should only call this if a work period was never started before,
        or if a previous work period was terminated with end_roe_work_period.
        
        If you call it under any other circumstances,
        CanNotStartWorkPeriodWithCurrent will be raised, something you can
        avoid by checking for a previously started and non-terminated period
        with current_roe_work_period_available

        Your start date must be after the end_date of the previous period, if
        it isn't InvalidRoeWorkPeriodStartDate is raised().
        """
        if self.current_roe_work_period_available():
            raise CanNotStartWorkPeriodWithCurrent()
        else:
            if self.get_num_roe_work_periods() == 0 or \
                    self.get_latest_roe_work_period()[END_OF_PERIOD] < \
                    start_date:
                self.__roe_work_periods.append((start_date, NO_ROE_END_DATE))
            else:
                raise InvalidRoeWorkPeriodStartDate()
        self._p_changed = True

    def end_roe_work_period(self, end_date):
        """Designate that a work period (for ROE purposes) has ended.

        The argument end_date must be of type datetime.date.
        The start date (of the period ending) is implicit, because you can not
        call end_roe_work_period, without first calling start_roe_work_period.
        If you do, call this out of order, NoCurrentRoeWorkPeriod will be
        raised. You can avoid that by checking
        current_roe_work_period_available()
        """
        # we're depending on this to raise NoCurrentRoeWorkPeriod if
        # there isn't an active period to end
        start_date = self.get_current_roe_work_period_start()
        self.__roe_work_periods[self.get_num_roe_work_periods()-1 ] = \
            (start_date, end_date)
        self._p_changed = True

    def reverse_started_roe_work_period(self):
        """An undo function for start_roe_work_period()

        No date needs to be provided, because the last call to
        start_roe_work_period is reversed. You can look up that date with
        get_current_roe_work_period_start()

        raises NoCurrentRoeWorkPeriod if reversing
        start_roe_work_period() doesn't make sense...
        """
        if self.current_roe_work_period_available():
            self.__roe_work_periods.pop()
            self._p_changed = True
        else:
            raise NoCurrentRoeWorkPeriod()

    def reverse_ended_roe_work_period(self):
        """An undo function for end_roe_work_period()

        No date needs to be provided, because the last call to
        end_roe_work_period is reversed. You can look up that date with
        get_latest_roe_work_period()

        raises NoEndedRoeWorkPeriodToReverse if there isn't a call to
        end_roe_work_period to reverse
        """
        if self.current_roe_work_period_available() or \
                self.get_num_roe_work_periods() == 0:
            raise NoEndedRoeWorkPeriodToReverse()
        else:
            start_date, end_date = self.get_latest_roe_work_period()
            self.__roe_work_periods.pop()
            self.start_roe_work_period(start_date)
            assert( self.current_roe_work_period_available() )
            self._p_changed = True

    def current_roe_work_period_available(self):
        """Check if there is a currently active roe work period, e.g.
        one that has a start date and not end date, e.g., one which
        was started with start_roe_work_period() but not yet terminated with
        end_roe_work_period()
        """
        num_periods = self.get_num_roe_work_periods()
        return num_periods>0 and \
            self.__roe_work_periods[num_periods-1][
            END_OF_PERIOD] == NO_ROE_END_DATE
    
    def get_current_roe_work_period_start(self):
        """Retrieve the start date (datetime.date) of the currently active
        roe work period (a current work period has no end date).

        If there isn't a current active period, this raises
        NoCurrentRoeWorkPeriod, but you could avoid that by just checking with
        current_roe_work_period_available().
        """
        if self.current_roe_work_period_available():
            return self.get_latest_roe_work_period()[START_OF_PERIOD]
        else:
            raise NoCurrentRoeWorkPeriod()

    def get_latest_roe_work_period(self):
        """Returns the most recent roe work period, as a tuple, with the first
        element being the start date (datetime.date) and the second element
        being the end date (datetime.date), if the latest roe work period
        is "current", one that hasn't ended yet, the second end date element
        will be NO_ROE_END_DATE.

        This raises RoeWorkPeriodNotExist if there are no ROE work periods
        (e.g. if start_roe_work_period has never been called), something you can
        avoid by checking with get_num_roe_work_periods
        """
        num_periods = self.get_num_roe_work_periods()
        if num_periods == 0:
            raise RoeWorkPeriodNotExist()
        else:
            return self.__roe_work_periods[num_periods-1]

    def roe_work_period_exists(self, start_date, end_date):
        """Check if a ROE work period with start_date and end_date
        (of type datetime.date) exists, if it does, return True, else False
        """
        for iter_start_date, iter_end_date in self.__roe_work_periods:
            if start_date == iter_start_date and end_date == iter_end_date:
                return True
        return False

    def get_num_roe_work_periods(self):
        """Get the number of ROR work periods, this includes the current
        period (if there is one) that was started with start_roe_work_period
        but not yet terminated by end_roe_work_period
        """
        return len(self.__roe_work_periods)

    def get_all_roe_work_periods(self, include_current=True):
        """A generator function that provides all of the ROE work periods.

        Each work period is a tuble of datetime.date values, the start date
        and the end date. The end date can also be NO_ROE_END_DATE

        include_current can be set to False (default is True) to have this
        function only include work periods that were ended, e.g. you won't
        get (start_date, NO_ROE_END_DATE) for the last entry if such an
        entry exists.
        """
        return ( (period_start, period_end)
                 for period_start, period_end in self.__roe_work_periods
                 if period_end != NO_ROE_END_DATE or include_current )

    def get_paystubs_for_roe_work_period(self, start_date, end_date):
        """Get all the paystubs for a given ROE work period.
        
        start_date and end_date of of type datetime.dat
        This period must exist, which means it must have been created with
        the start_roe_work_period and end_roe_work_period functions. If the
        ROE period does not exist, this function raises RoeWorkPeriodNotExist,
        a situation you can avoid by checking with roe_work_period_exists
        or simply getting your period start and end dates from
        get_lastest_roe_work_period() or get_all_roe_work_periods()
        """
        if self.roe_work_period_exists(start_date, end_date):
            return self.get_bounded_paystubs(start_date, end_date)
        else:
            raise RoeWorkPeriodNotExist()

    def first_paydate_by_paystub(self, answer_for_none=None):
        return (
            answer_for_none if len(self.paystubs) == 0
            else self.paystubs[0].payday.paydate )

    def get_vacation_pay_rate(self, as_of_date=None):
        # look up the vacation pay rate in terms of the time of service,
        # which is calculated as some particular as_of_date (defaults to today)
        # minus the start date
        #
        # start date comes from the ROE support if present in the employee
        # with a start date, otherwise we go with the date of the first
        # paystub found. (if there is one, and if we use the same as_of_date
        # so time of service comes out to zero)
        #
        # There is a flaw here though -- if an ROE was issued for a leave
        # of absense or seasonal termination under Manitoba law, time of
        # service still accumulates, so this will be wrong.
        #
        # logic for that kind of thing will have to be per province once
        # it is developed...
        if as_of_date == None:
            as_of_date = date.today()
        return self.province.get_vacation_pay_rate_for_time_for_service(
            self.first_paydate_by_paystub(as_of_date)
            if not self.current_roe_work_period_available()
            else self.get_current_roe_work_period_start(),

            as_of_date ) # end get_vacation_pay_rate_for_time_for_service
    
            

class RoeWorkPeriodsAlreadyInit(Exception):
    pass

class NoCurrentRoeWorkPeriod(Exception):
    pass

class NoEndedRoeWorkPeriodToReverse(Exception):
    pass

class CanNotStartWorkPeriodWithCurrent(Exception):
    pass

class RoeWorkPeriodNotExist(Exception):
    pass

class InvalidRoeWorkPeriodStartDate(Exception):
    pass
