import unittest
import os
import shutil
import glob
import filecmp
import sys

from bokeep.book import BoKeepBookSet
from bokeep.plugins.payroll.plain_text_payroll import \
    payroll_runtime, payroll_has_payday_serial, payroll_employee_command, \
    handle_backend_command

from test_bokeep_book import create_filestorage_backed_bookset_from_file
from test_payroll_employee import PayrollTestCaseSetup, TESTBOOK


PAYROLL_CONFIG_DATA_SYS_PATH_POS = 0

class wageTestCase(PayrollTestCaseSetup):     
    #This runs before EACH test function, not simply once for the whole test 
    #case
    def setUp(self):
        PayrollTestCaseSetup.setUp(self)
        sys.path.insert(
            PAYROLL_CONFIG_DATA_SYS_PATH_POS,
            "test_payroll_wages_config_data/")
    
    def tearDown(self):
        sys.path.pop(PAYROLL_CONFIG_DATA_SYS_PATH_POS)
        PayrollTestCaseSetup.tearDown(self)
    
    def testSinglerun(self):
        from payday_data import paydate, payday_serial
        payroll_runtime(TESTBOOK, False, bookset=self.books)
        # implicit selfbooks.close()

        self.books = create_filestorage_backed_bookset_from_file(
            self.filestorage_file, False)
        
        # FIXME, payroll_runtime isn't creating PaystubPrint.txt
        # self.assert_(filecmp.cmp("PaystubPrint.txt", "tests/test_payroll_wages_PaystubPrint.txt"))       

        # FIXME, this test can't be done because we can't pass our own
        # bookset to it..
        #we should also have an entry for this paydate now.
        #self.assert_(payroll_has_payday_serial(TESTBOOK, paydate, payday_serial))

    def testDoublerun(self):
        payroll_runtime(TESTBOOK, False, bookset=self.books)
        # implicit self.books.close()

        self.books = create_filestorage_backed_bookset_from_file(
            self.filestorage_file, False)
        self.assert_( self.books.has_book(TESTBOOK) )

        payroll_runtime(TESTBOOK, False, bookset=self.books)
        # implicit bookset.close()

        self.books = create_filestorage_backed_bookset_from_file(
            self.filestorage_file, False)

        # FIXME, payroll_runtime isn't creating PaystubPrint.txt
	#self.assert_(filecmp.cmp("PaystubPrint.txt", "./wages_testing/PaystubPrint1.txt"))

    def testTimesheeting(self):
        #standard "no timesheets" run first
        payroll_runtime(TESTBOOK, False, bookset=self.books)
        # implicit self.books.close()        
        
        self.books = create_filestorage_backed_bookset_from_file(
            self.filestorage_file, False)

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

            payroll_employee_command(TESTBOOK, self.books, "add",
                                     payroll_info_list )
            # implicit bookset.close()
            self.books = create_filestorage_backed_bookset_from_file(
            self.filestorage_file, False)

        payroll_runtime(TESTBOOK, False, bookset=self.books)
        # implicit bookset.close()

        self.books = create_filestorage_backed_bookset_from_file(
            self.filestorage_file, False)

        # FIXME, payroll_runtime isn't creating PaystubPrint.txt
	#self.assert_(filecmp.cmp("PaystubPrint.txt", "tests/test_payroll_wages_PaystubPrint2.txt"))

        
if __name__ == "__main__":
    unittest.main()

