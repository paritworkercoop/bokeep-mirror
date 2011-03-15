# Copyright (C) 2011  ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
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
from datetime import date
from decimal import Decimal
import unittest


# bo-keep imports
from bokeep.plugins.payroll.payroll import Remittance

# bo-keep test imports
from tests.test_payroll_wages import PayrollPaydayTestCaseSetup

class remittTestCase(PayrollPaydayTestCaseSetup):
    def setUp(self):
        PayrollPaydayTestCaseSetup.setUp(self)
        self.remitt = Remittance(self.payroll_plugin)
        self.remitt.remitt_date = date(2009, 5, 15)
        self.remitt.set_period_start_and_end_from_remmit_date()
        self.perform_single_run()

    def test_remitt(self):
        self.assertEquals(self.remitt.num_employees(), 2)
        self.assertEquals(self.remitt.get_gross_pay(), Decimal('1033.60') )
        self.assertEquals(self.remitt.num_paydays(), 1)
        self.assertEquals(self.remitt.get_remitt(), Decimal('181.64') )
        self.assertEquals(self.remitt.period_start, date(2009, 4, 1))
        self.assertEquals(self.remitt.period_end, date(2009, 4, 30))
                          

if __name__ == "__main__":
    unittest.main()
