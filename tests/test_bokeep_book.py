# python
from unittest import TestCase, main

# zopedb
import ZODB.config
import transaction

# bokeep
from bokeep.book import BoKeepBookSet, BoKeepBook


TESTBOOK = "testbook"
BOOKS_CONF = "tests/test_books.conf"
class TestBoKeepBookSetup(TestCase):
    def setUp(self):
        self.books = BoKeepBookSet(BOOKS_CONF)
        if self.books.has_book(TESTBOOK):
            self.books.remove_book(TESTBOOK)

    def tearDown(self):
        if self.books.has_book(TESTBOOK):
            self.books.remove_book(TESTBOOK)
        self.books.close()

class TestBoKeepBookAddChanged(TestBoKeepBookSetup):

    def test_p_changed_odd(self):
        self.books.dbroot[TESTBOOK] = book = BoKeepBook(TESTBOOK)
        self.assert_(self.books.dbroot._p_changed)
        transaction.get().commit()
        self.assertFalse(self.books.dbroot._p_changed)
        self.books.dbroot[TESTBOOK].boo = "boo"
        self.assert_(self.books.dbroot[TESTBOOK]._p_changed)



class TestBoKeepBookWithAdd(TestBoKeepBookSetup):
    def setUp(self):
        TestBoKeepBookSetup.setUp(self)
        self.test_book_1 = self.books.add_book(TESTBOOK)

    def test_book_enabled_attr(self):
        self.assert_(hasattr(self.books.get_book(TESTBOOK), 'enabled_modules'))

    def test_book_enabled_attr_after_close(self):
        self.books.close_primary_connection()
        self.books.dbcon = self.books.get_new_dbcon()
        self.books.dbroot = self.books.dbcon.root()
        self.test_book_enabled_attr()
        self.books.close_primary_connection()
        self.books.close()
    
        self.books.zodb = ZODB.config.databaseFromURL(BOOKS_CONF)
        self.books.dbcon = self.books.zodb.open()
        self.books.dbroot = self.books.dbcon.root()
        self.test_book_enabled_attr()


if __name__ == "__main__":
    main()
