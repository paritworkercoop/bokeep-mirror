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

