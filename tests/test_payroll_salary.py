import unittest
import os
import shutil
import glob
import filecmp
import sys

from bokeep.config import get_database_cfg_file
from bokeep.book import BoKeepBookSet
from bokeep.modules.payroll.plain_text_payroll import \
    payroll_runtime, payroll_has_payday_serial, handle_backend_command

SALARY_TEST_BOOKNAME = 'paytest'
TEST_ZOPEDB_CONFIG = "tests/test_books.conf"

PAYROLL_CONFIG_DATA_SYS_PATH_POS = 0

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

        #generate the books file
        bookset = BoKeepBookSet( TEST_ZOPEDB_CONFIG )
        self.assertFalse( bookset.has_book(SALARY_TEST_BOOKNAME) )
        bookset.add_book(SALARY_TEST_BOOKNAME)
	book = bookset.get_book(SALARY_TEST_BOOKNAME)

        #set our backend to serialfile
        handle_backend_command(book, ["set",
                                      "bokeep.backend_modules.serialfile"])

        bookset.close()
        sys.path.insert(
            PAYROLL_CONFIG_DATA_SYS_PATH_POS,
            "tests/test_payroll_salary_config_data/")

    def tearDown(self):
        sys.path.pop(PAYROLL_CONFIG_DATA_SYS_PATH_POS)


    def testSinglerun(self):
        from payday_data import paydate, payday_serial
        bookset = BoKeepBookSet(TEST_ZOPEDB_CONFIG)
        payroll_runtime(SALARY_TEST_BOOKNAME, False, bookset=bookset)
        # implicit bookset.close()

        # FIXME, call to payroll_runtime can't result in creation of
        # PaystubPrint.txt
        #self.assert_(filecmp.cmp("PaystubPrint.txt",
        #                         "tests/test_payroll_salary_PaystubPrint.txt") )

        # FIXME, this test can't be done because we can't pass our own
        # bookset to it..
        #we should also have an entry for this paydate now.
        #self.assert_(payroll_has_payday_serial(
        #        SALARY_TEST_BOOKNAME, paydate, payday_serial))
        
    def testDoublerun(self):
        bookset = BoKeepBookSet(TEST_ZOPEDB_CONFIG)
        payroll_runtime(SALARY_TEST_BOOKNAME, False, bookset=bookset)
        # implicit bookset.close()
        
        bookset = BoKeepBookSet(TEST_ZOPEDB_CONFIG)
        payroll_runtime(SALARY_TEST_BOOKNAME, False, bookset=bookset)
        # implicit bookset.close()

        # FIXME, this test can't be done, call to payroll_runtime can't result in
        # creation of PaystubPrint.txt
	#self.assert_(filecmp.cmp("PaystubPrint.txt",
        #                         "tests/test_payroll_salary_PaystubPrint.txt" ))

if __name__ == "__main__":
    unittest.main()

