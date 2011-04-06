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
from unittest import main
from decimal import Decimal

# bo-keep imports
from bokeep.plugins.payroll.plain_text_payroll import year_to_date_sum_of_class
from bokeep.plugins.payroll.payroll import PaystubIncomeLine

# bo-keep test imports
from tests.test_payroll_VacPay import ComplexVacationPayoutSetup

class TestYTD(ComplexVacationPayoutSetup):
    def test_ytd_paystub_lines(self):
        for cls, value_str in ( (PaystubIncomeLine, 416),
                                ): # tuple
            self.assertEquals(
                year_to_date_sum_of_class(cls)(self.paystub_three),
                Decimal(value_str) )

if __name__ == '__main__':
    main()
