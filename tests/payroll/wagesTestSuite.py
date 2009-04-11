import unittest
import os
import shutil
import glob
import filecmp

from bokeep.config import get_database_cfg_file
from bokeep.book import BoKeepBookSet
from bo_keep_payroll import payroll_runtime, payroll_has_payday_serial, payroll_employee_command
from bo_keep_module_control import handle_backend_command

WAGES_TEST_BOOKNAME = 'paytest'

class wageTestCase(unittest.TestCase):

        
    #This runs before EACH test function, not simply once for the whole test 
    #case
    def setUp(self):
        #nuke data from prior runs
        if os.path.exists('PaystubPrint.txt'):
            os.remove('PaystubPrint.txt')

        fs_files = glob.glob('*.fs*')
        for f in fs_files:
            os.remove(f)

        fs_files = glob.glob('wages_testing/*.py')
        for f in fs_files:
            shutil.copy(f, '.')

        #generate the books file
        bookset = BoKeepBookSet( get_database_cfg_file() )
        assert( not bookset.has_book(WAGES_TEST_BOOKNAME) )
        bookset.add_book(WAGES_TEST_BOOKNAME)
	book = bookset.get_book(WAGES_TEST_BOOKNAME)

        #set our backend to serialfile
        handle_backend_command(book, ["set", "bokeep.backend_modules.serialfile"])

        bookset.close()

    def testSinglerun(self):
        from payday_data import paydate, payday_serial

        payroll_runtime(WAGES_TEST_BOOKNAME, False)        
        assert(filecmp.cmp("PaystubPrint.txt", "./wages_testing/PaystubPrint1.txt"))       

        #we should also have an entry for this paydate now.
        assert(payroll_has_payday_serial(WAGES_TEST_BOOKNAME, paydate, payday_serial))

    def testDoublerun(self):
        payroll_runtime(WAGES_TEST_BOOKNAME, False)        
        payroll_runtime(WAGES_TEST_BOOKNAME, False)
	assert(filecmp.cmp("PaystubPrint.txt", "./wages_testing/PaystubPrint1.txt"))

    def testTimesheeting(self):
        #standard "no timesheets" run first
        payroll_runtime(WAGES_TEST_BOOKNAME, False)        

        #add timesheets
        payroll_employee_command(WAGES_TEST_BOOKNAME, None, "add", ["timesheet", "george costanza", "April 5, 2009", 20, "12-8 server"])
        payroll_employee_command(WAGES_TEST_BOOKNAME, None, "add", ["timesheet", "george costanza", "April 6, 2009", 30, "morning admin"])
        payroll_employee_command(WAGES_TEST_BOOKNAME, None, "add", ["timesheet", "susie", "April 7, 2009", 15, "morning line"])
        payroll_employee_command(WAGES_TEST_BOOKNAME, None, "add", ["timesheet", "george costanza", "April 8, 2009", 12, "evening sf"])
        payroll_employee_command(WAGES_TEST_BOOKNAME, None, "add", ["timesheet", "susie", "April 8, 2009", 5, "morning sf"])
        payroll_employee_command(WAGES_TEST_BOOKNAME, None, "add", ["timesheet", "george costanza", "April 19, 2009", 4, "misc"])
        payroll_employee_command(WAGES_TEST_BOOKNAME, None, "add", ["timesheet", "susie", "April 19, 2009", 4, "extra labour"])
        payroll_employee_command(WAGES_TEST_BOOKNAME, None, "add", ["timesheet", "susie", "April 20, 2009", 15, "morning grocery"])

        payroll_runtime(WAGES_TEST_BOOKNAME, False)        
	assert(filecmp.cmp("PaystubPrint.txt", "./wages_testing/PaystubPrint2.txt"))

        
class wageTestSuite(unittest.TestSuite):
    def __init__(self):
        unittest.TestSuite.__init__(self,map(wageTestCase, ()))

if __name__ == "__main__":
    unittest.main()

