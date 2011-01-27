# Copyright (C) 2010  ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
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

import unittest
import os
import glob
import filecmp

#from bokeep.config import get_database_cfg_file
from bokeep.book import BoKeepBookSet
from bokeep.plugins.payroll.plain_text_payroll \
    import payroll_add_employee, payroll_get_employees


from test_bokeep_book import BoKeepWithBookSetup, TESTBOOK

PAYROLL_PLUGIN = 'bokeep.plugins.payroll'

class PayrollTestCaseSetup(BoKeepWithBookSetup):
    def setUp(self):
        BoKeepWithBookSetup.setUp(self)
        self.books.get_book(TESTBOOK).add_module(PAYROLL_PLUGIN)
        self.books.get_book(TESTBOOK).enable_module(PAYROLL_PLUGIN)
        self.payroll_plugin = self.books.get_book(TESTBOOK).get_module(
            PAYROLL_PLUGIN)
        payroll_add_employee(TESTBOOK, "george costanza", self.books)
        payroll_add_employee(TESTBOOK, "susie", self.books)

class empTestCase(PayrollTestCaseSetup):
    def testEmpAddAndGet(self):
        self.assert_( self.books.has_book(TESTBOOK) )
        
        emplist = payroll_get_employees(TESTBOOK, self.books)[0] 
        FIRST_EMP = 'george costanza'
        SECOND_EMP = 'susie'
        empsWeWant = [FIRST_EMP, SECOND_EMP]

        self.assertEquals(len(empsWeWant), len(emplist))
        self.assertFalse( emplist[FIRST_EMP] == None)
        self.assertFalse( emplist[SECOND_EMP] == None)

if __name__ == "__main__":
    unittest.main()

