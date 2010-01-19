import unittest
import os
import shutil
import glob
import filecmp
import sys

from bokeep.config import get_database_cfg_file
from bokeep.book import BoKeepBookSet
from bokeep.modules.payroll.plain_text_payroll import \
    payroll_runtime, payroll_has_payday_serial, payroll_employee_command, \
    handle_backend_command

WAGES_TEST_BOOKNAME = 'paytest'

TEST_ZOPEDB_CONFIG = "tests/test_books.conf"

PAYROLL_CONFIG_DATA_SYS_PATH_POS = 0

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

        #generate the books file
        bookset = BoKeepBookSet( TEST_ZOPEDB_CONFIG  )
        self.assertFalse( bookset.has_book(WAGES_TEST_BOOKNAME) )
        bookset.add_book(WAGES_TEST_BOOKNAME)
	book = bookset.get_book(WAGES_TEST_BOOKNAME)

        #set our backend to serialfile
        handle_backend_command(book, ["set", "bokeep.backend_modules.serialfile"])

        bookset.close()

        sys.path.insert(
            PAYROLL_CONFIG_DATA_SYS_PATH_POS,
            "tests/test_payroll_wages_config_data/")
    
    def tearDown(self):
        sys.path.pop(PAYROLL_CONFIG_DATA_SYS_PATH_POS)
    
    def testSinglerun(self):
        from payday_data import paydate, payday_serial
        bookset = BoKeepBookSet(TEST_ZOPEDB_CONFIG)
        payroll_runtime(WAGES_TEST_BOOKNAME, False, bookset=bookset)
        # implicit bookset.close()
        
        # FIXME, payroll_runtime isn't creating PaystubPrint.txt
        # self.assert_(filecmp.cmp("PaystubPrint.txt", "tests/test_payroll_wages_PaystubPrint.txt"))       

        # FIXME, this test can't be done because we can't pass our own
        # bookset to it..
        #we should also have an entry for this paydate now.
        #self.assert_(payroll_has_payday_serial(WAGES_TEST_BOOKNAME, paydate, payday_serial))

    def testDoublerun(self):
        bookset = BoKeepBookSet(TEST_ZOPEDB_CONFIG)
        payroll_runtime(WAGES_TEST_BOOKNAME, False, bookset=bookset)
        # implicit bookset.close()
        
        bookset = BoKeepBookSet(TEST_ZOPEDB_CONFIG)
        payroll_runtime(WAGES_TEST_BOOKNAME, False, bookset=bookset)
        # implicit bookset.close()

        # FIXME, payroll_runtime isn't creating PaystubPrint.txt
	#self.assert_(filecmp.cmp("PaystubPrint.txt", "./wages_testing/PaystubPrint1.txt"))

    def testTimesheeting(self):
        bookset = BoKeepBookSet(TEST_ZOPEDB_CONFIG)
        #standard "no timesheets" run first
        payroll_runtime(WAGES_TEST_BOOKNAME, False, bookset=bookset)
        # implicit bookset.close()
        
        

        for payroll_info_list in (
            ["timesheet", "george costanza", "April 5, 2009", 20,
             "12-8 server"],
            ["timesheet", "george costanza", "April 6, 2009", 30,
             "morning admin"],
            ["timesheet", "susie", "April 7, 2009", 15, "morning line"],
            ["timesheet", "george costanza", "April 8, 2009", 12, "evening sf"],
            ["timesheet", "susie", "April 8, 2009", 5, "morning sf"],
            ["timesheet", "george costanza", "April 19, 2009", 4, "misc"],
            ["timesheet", "susie", "April 19, 2009", 4, "extra labour"],
            ["timesheet", "susie", "April 20, 2009", 15, "morning grocery"] ):

            bookset = BoKeepBookSet(TEST_ZOPEDB_CONFIG)
            payroll_employee_command(WAGES_TEST_BOOKNAME, bookset, "add",
                                     payroll_info_list )
            # implicit bookset.close()

        bookset = BoKeepBookSet(TEST_ZOPEDB_CONFIG)
        payroll_runtime(WAGES_TEST_BOOKNAME, False, bookset=bookset)
        # implicit bookset.close()

        # FIXME, payroll_runtime isn't creating PaystubPrint.txt
	#self.assert_(filecmp.cmp("PaystubPrint.txt", "tests/test_payroll_wages_PaystubPrint2.txt"))

        
if __name__ == "__main__":
    unittest.main()

