from unittest import TestCase, main
from persistent.list import PersistentList

from bokeep.plugins.payroll.canada.timesheet import Timesheet

from test_bokeep_book import BoKeepBasicTestSetup

class TestTwoListsOfUnpersistableCrap(BoKeepBasicTestSetup):
    def setUp(self):
        BoKeepBasicTestSetup.setUp(self)
        self.p_list_1 = PersistentList()
        self.p_list_2 = PersistentList()
        timelog = Timesheet(1, 2, 3)
        self.p_list_1.append(timelog)
        self.p_list_2.append(timelog)
        self.books.get_dbhandle().set_sub_database(
            'haha', (self.p_list_1, self.p_list_2) )

    def test_same_lists(self):
        self.assertEquals(self.p_list_1, self.p_list_2)
        self.assertEquals(self.p_list_1[0], self.p_list_2[0])

if __name__ == "__main__":
    main()
