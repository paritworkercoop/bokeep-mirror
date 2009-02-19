import unittest
import os
import shutil
import glob
from bokeep.config import get_database_cfg_file
from bokeep.book import BoKeepBookSet
from bo_keep_payroll import payroll_runtime
#from bo_keep_module_control import handle_backend_command

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

        #generate the books file
        bookset = BoKeepBookSet( get_database_cfg_file() )
        assert( not bookset.has_book(SALARY_TEST_BOOKNAME) )
        bookset.add_book(SALARY_TEST_BOOKNAME)
#        book = bookset.get_book(SALARY_TEST_BOOKNAME)

        #set our backend to serialfile
#        handle_backend_command(book, ["set", "bokeep.backend_modules.serialfile"])

        bookset.close_primary_connection()

    def testSinglerun(self):
        payroll_runtime(SALARY_TEST_BOOKNAME)

    def testOranges(self):
        pass


class salaryTestSuite(unittest.TestSuite):
    def __init__(self):
        unittest.TestSuite.__init__(self,map(salaryTestCase, ("testApples", "testOranges")))

if __name__ == "__main__":
    unittest.main()

