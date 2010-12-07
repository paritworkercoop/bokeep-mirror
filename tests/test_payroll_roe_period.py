# python imports
from datetime import date, timedelta
from unittest import TestCase, main

from bokeep.plugins.payroll.canada.employee import \
    Employee, NO_ROE_END_DATE, RoeWorkPeriodsAlreadyInit, \
    CanNotStartWorkPeriodWithCurrent, InvalidRoeWorkPeriodStartDate, \
    NoCurrentRoeWorkPeriod, NoEndedRoeWorkPeriodToReverse

ONE_DAY = timedelta(days=1)
THIRTY_DAYS = timedelta(days=30)

class RoePeriodTestSetup(TestCase):
    def setUp(self):
        self.emp = Employee("test employee")
        self.day_one = date(2010, 01, 01)
        self.latest_start = self.day_one
        self.day_two = self.day_one + ONE_DAY
        self.emp.start_roe_work_period(self.day_one)

    def test_double_init_fail(self):
        self.assertRaises(
            RoeWorkPeriodsAlreadyInit,
            self.emp.init_roe_work_periods )

    def test_latest_start_present_via_last(self):
        self.assertEquals(self.emp.get_latest_roe_work_period()[0],
                          self.latest_start )

    def test_latest_start_present_via_generator(self):
        all_periods = list(self.emp.get_all_roe_work_periods())
        all_periods_len = len(all_periods)
        num_periods = self.emp.get_num_roe_work_periods()
        self.assertEquals(all_periods_len, num_periods)
        self.assertEquals(all_periods[all_periods_len-1][0],
                          self.latest_start )

class RoePeriodRightAfterStartTest(RoePeriodTestSetup):
    def test_current_avail(self):
        self.assert_(self.emp.current_roe_work_period_available() )
        
    def test_new_period_start_before_close_fail(self):
        self.assertRaises(
            CanNotStartWorkPeriodWithCurrent,
            self.emp.start_roe_work_period,
            self.day_two )

    def test_start_reverse(self):
        self.emp.reverse_started_roe_work_period()
        self.assertFalse(self.emp.current_roe_work_period_available())
    
    def test_end_reverse_fail(self):
        self.assertRaises(
            NoEndedRoeWorkPeriodToReverse,
            self.emp.reverse_ended_roe_work_period )

class RoePeriodRightStartAndEndTest(RoePeriodTestSetup):
    def setUp(self):
        RoePeriodTestSetup.setUp(self)
        self.emp.end_roe_work_period(self.day_two)
        
    def test_new_period_start_on_end_day_fail(self):
        self.assertRaises(
            InvalidRoeWorkPeriodStartDate,
            self.emp.start_roe_work_period,
            self.day_two )

    def test_new_period_start_early_fail(self):
        for day_try in (self.day_one, self.day_one - THIRTY_DAYS):
            self.assertRaises(
                InvalidRoeWorkPeriodStartDate,
                self.emp.start_roe_work_period,
                day_try)
    
    def test_double_end_fail(self):
        self.assertRaises(
            NoCurrentRoeWorkPeriod,
            self.emp.end_roe_work_period,
            self.day_two )

    def test_reverse_end(self):
        self.emp.reverse_ended_roe_work_period()
        self.test_latest_start_present_via_last()

    def test_start_reverse_fail(self):
        self.assertRaises(
            NoCurrentRoeWorkPeriod,
            self.emp.reverse_started_roe_work_period )

if __name__ == '__main__':
    main()
