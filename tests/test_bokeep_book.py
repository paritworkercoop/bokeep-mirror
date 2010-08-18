# python
from unittest import TestCase, main

# zopedb
import ZODB.config
import transaction

# bokeep
from bokeep.book import BoKeepBookSet, BoKeepBook, BOOKS_SUB_DB_KEY


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
        self.books.dbroot[BOOKS_SUB_DB_KEY][TESTBOOK] = book = \
            BoKeepBook(TESTBOOK)
        self.books.dbroot._p_changed = True
        self.assert_(self.books.dbroot._p_changed)
        transaction.get().commit()
        self.assertFalse(self.books.dbroot._p_changed)
        self.books.dbroot[BOOKS_SUB_DB_KEY][TESTBOOK].boo = "boo"
        self.books.dbroot._p_changed = True
        self.assert_(self.books.dbroot[BOOKS_SUB_DB_KEY][TESTBOOK]._p_changed)



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
