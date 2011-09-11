from unittest import TestCase, main
from persistent.list import PersistentList
import transaction

from bokeep.plugins.payroll.canada.timesheet import Timesheet

from test_bokeep_book import BoKeepBasicTestSetup, \
    create_filestorage_backed_bookset_from_file

class TestTwoListsOfUnpersistableCrapSetup(BoKeepBasicTestSetup):
    def setUp(self):
        BoKeepBasicTestSetup.setUp(self)
        p_list_1 = PersistentList()
        p_list_2 = PersistentList()
        timelog = Timesheet(1, 2, 3)
        p_list_1.append(timelog)
        p_list_2.append(timelog)
        self.books.get_dbhandle().set_sub_database(
            'haha', (p_list_1, p_list_2) )
        self.books.close()
        self.books_new = create_filestorage_backed_bookset_from_file(
            self.filestorage_file, False)

    def test_same_lists(self):
        (p_list_1, p_list_2) = \
            self.books_new.get_dbhandle().get_sub_database('haha')
        self.assertEquals(p_list_1, p_list_2)
        self.assertEquals(p_list_1[0], p_list_2[0])

if __name__ == "__main__":
    main()
