import unittest
import os
import shutil
import glob
import filecmp
import sys

from bokeep.book import BoKeepBookSet
from bokeep.plugins.payroll.plain_text_payroll import \
    payroll_runtime, payroll_has_payday_serial, handle_backend_command

from test_bokeep_book import create_filestorage_backed_bookset_from_file
from test_payroll_employee import PayrollTestCaseSetup, TESTBOOK

PAYROLL_CONFIG_DATA_SYS_PATH_POS = 0

class salaryTestCase(PayrollTestCaseSetup):

        
    #This runs before EACH test function, not simply once for the whole test 
    #case
    def setUp(self):
        PayrollTestCaseSetup.setUp(self)
        sys.path.insert(
            PAYROLL_CONFIG_DATA_SYS_PATH_POS,
            "test_payroll_salary_config_data/")

    def tearDown(self):
        sys.path.pop(PAYROLL_CONFIG_DATA_SYS_PATH_POS)
        PayrollTestCaseSetup.tearDown(self)

    def testSinglerun(self):
        from payday_data import paydate, payday_serial
        payroll_runtime(TESTBOOK, False, bookset=self.books)
        # implicit bookset.close()

        self.books = create_filestorage_backed_bookset_from_file(
            self.filestorage_file, False)

        # FIXME, call to payroll_runtime can't result in creation of
        # PaystubPrint.txt
        #self.assert_(filecmp.cmp("PaystubPrint.txt",
        #                         "tests/test_payroll_salary_PaystubPrint.txt") )

        # FIXME, this test can't be done because we can't pass our own
        # bookset to it..
        #we should also have an entry for this paydate now.
        #self.assert_(payroll_has_payday_serial(
        #        TESTBOOK, paydate, payday_serial))
        
    def testDoublerun(self):
        payroll_runtime(TESTBOOK, False, bookset=self.books)
        # implicit bookset.close()
        
        self.books = create_filestorage_backed_bookset_from_file(
            self.filestorage_file, False)
        self.assert_( self.books.has_book(TESTBOOK) )
        payroll_runtime(TESTBOOK, False, bookset=self.books)
        # implicit self.books.close()

        self.books = create_filestorage_backed_bookset_from_file(
            self.filestorage_file, False)
        # FIXME, this test can't be done, call to payroll_runtime can't result in
        # creation of PaystubPrint.txt
	#self.assert_(filecmp.cmp("PaystubPrint.txt",
        #                         "tests/test_payroll_salary_PaystubPrint.txt" ))

if __name__ == "__main__":
    unittest.main()

