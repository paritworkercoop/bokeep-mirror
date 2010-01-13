import unittest
import os
import glob
import filecmp

#from bokeep.config import get_database_cfg_file
from bokeep.book import BoKeepBookSet
from bokeep.bo_keep_payroll import payroll_add_employee, payroll_get_employees

EMP_TEST_BOOKNAME = 'paytest'

TEST_ZOPEDB_CONFIG = "tests/test_books.conf"

class empTestCase(unittest.TestCase):

        
    #This runs before EACH test function, not simply once for the whole test 
    #case
    def setUp(self):
        fs_files = glob.glob('*.fs*')
        for f in fs_files:
            os.remove(f)

        #generate the books file
        bookset = BoKeepBookSet( TEST_ZOPEDB_CONFIG)
        self.assertFalse( bookset.has_book(EMP_TEST_BOOKNAME) )
        bookset.add_book(EMP_TEST_BOOKNAME)
	book = bookset.get_book(EMP_TEST_BOOKNAME)

        bookset.close()

    def testEmpAddAndGet(self):
        bookset = BoKeepBookSet( TEST_ZOPEDB_CONFIG)
        payroll_add_employee(EMP_TEST_BOOKNAME, "george costanza", bookset)
        payroll_add_employee(EMP_TEST_BOOKNAME, "susie", bookset)
        
        emplist = payroll_get_employees(EMP_TEST_BOOKNAME, bookset)[0] 
        FIRST_EMP = 'george costanza'
        SECOND_EMP = 'susie'
        empsWeWant = [FIRST_EMP, SECOND_EMP]

        self.assertEquals(len(empsWeWant), len(emplist))
        self.assertFalse( emplist[FIRST_EMP] == None)
        self.assertFalse( emplist[SECOND_EMP] == None)

        bookset.close()
#        for emp in emplist:
#            if not(str(emp) == str(empsWeWant print 'emp : ' + str(emp)
        

        

        
#class empTestSuite(unittest.TestSuite):
#    def __init__(self):
#        unittest.TestSuite.__init__(self,map(empTestCase, ()))

if __name__ == "__main__":
    unittest.main()

