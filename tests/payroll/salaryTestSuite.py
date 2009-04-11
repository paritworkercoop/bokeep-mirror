import unittest
import os
import shutil
import glob
import filecmp

from bokeep.config import get_database_cfg_file
from bokeep.book import BoKeepBookSet
from bokeep.bo_keep_payroll import payroll_runtime, payroll_has_payday_serial
from bo_keep_module_control import handle_backend_command

SALARY_TEST_BOOKNAME = 'paytest'

class salaryTestCase(unittest.TestCase):

        
    #This runs before EACH test function, not simply once for the whole test 
    #case
    def setUp(self):
        #nuke data from prior runs
        if os.path.exists('PaystubPrint.txt'):
            os.remove('PaystubPrint.txt')

        fs_files = glob.glob('*.fs*')
        for f in fs_files:
            os.remove(f)

        fs_files = glob.glob('salary_testing/*.py')
        for f in fs_files:
            shutil.copy(f, '.')

        #generate the books file
        bookset = BoKeepBookSet( get_database_cfg_file() )
        assert( not bookset.has_book(SALARY_TEST_BOOKNAME) )
        bookset.add_book(SALARY_TEST_BOOKNAME)
	book = bookset.get_book(SALARY_TEST_BOOKNAME)

        #set our backend to serialfile
        handle_backend_command(book, ["set", "bokeep.backend_modules.serialfile"])

        bookset.close()

    def testSinglerun(self):
        from payday_data import paydate, payday_serial

        payroll_runtime(SALARY_TEST_BOOKNAME, False)        
        assert(filecmp.cmp("PaystubPrint.txt", "./salary_testing/PaystubPrint1.txt"))       

        #we should also have an entry for this paydate now.
        assert(payroll_has_payday_serial(SALARY_TEST_BOOKNAME, paydate, payday_serial))

    def testDoublerun(self):
        payroll_runtime(SALARY_TEST_BOOKNAME, False)        
        payroll_runtime(SALARY_TEST_BOOKNAME, False)
	assert(filecmp.cmp("PaystubPrint.txt", "./salary_testing/PaystubPrint1.txt"))

class salaryTestSuite(unittest.TestSuite):
    def __init__(self):
        unittest.TestSuite.__init__(self,map(salaryTestCase, ()))

if __name__ == "__main__":
    unittest.main()

