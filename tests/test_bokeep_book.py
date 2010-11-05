# python
from unittest import TestCase, main
from os.path import exists
from os import remove
from glob import glob
from tempfile import NamedTemporaryFile

# zopedb
from ZODB.FileStorage import FileStorage
from ZODB import DB
import transaction


# bokeep
from bokeep.book import BoKeepBookSet, BoKeepBook, BOOKS_SUB_DB_KEY

TESTBOOK = "testbook"

def create_tmp_filestorage_filename():
    tmp = NamedTemporaryFile(
            suffix='.fs',
            prefix='tmp_bokeep_db_',
            dir='.')
    filestorage_file = tmp.name
    tmp.close()
    return filestorage_file

def create_filestorage_backed_bookset_from_file(filestorage_path):
    fs = FileStorage(filestorage_path, create=True )
    return BoKeepBookSet( DB(fs) )

class BoKeepBasicTestSetup(TestCase):
    def setUp(self):
        self.filestorage_file = create_tmp_filestorage_filename()
        self.assertFalse( exists(self.filestorage_file) )
        self.books = create_filestorage_backed_bookset_from_file(
            self.filestorage_file)
        transaction.get().commit()

    def tearDown(self):
        self.books.close()
        for file_name in glob(self.filestorage_file + '*'):
            remove(file_name)

#         self.assertFalse(self.books.has_book(TESTBOOK))
#        self.test_book_1 = self.books.add_book(TESTBOOK)
#        # no way to test  self.books.get_book(TESTBOOK) anymore...

class TestBoKeepBookAddChanged(BoKeepBasicTestSetup):
    def test_p_changed_odd(self):
        self.books.get_dbhandle().\
            get_sub_database(BOOKS_SUB_DB_KEY)[TESTBOOK] = book = \
            BoKeepBook(TESTBOOK)
        self.books.get_dbhandle().dbroot._p_changed = True
        self.assert_(self.books.get_dbhandle().dbroot._p_changed)
        transaction.get().commit()
        self.assertFalse(self.books.get_dbhandle().dbroot._p_changed)
        self.books.get_dbhandle().\
            get_sub_database(BOOKS_SUB_DB_KEY)[TESTBOOK].boo = "boo"
        self.books.get_dbhandle().dbroot._p_changed = True
        self.assert_(self.books.get_dbhandle().dbroot._p_changed)

class BoKeepWithBookSetup(BoKeepBasicTestSetup):
    def setUp(self):
        BoKeepBasicTestSetup.setUp(self)
        self.test_book_1 = self.books.add_book(TESTBOOK)

class TestBoKeepBookWithAdd(BoKeepWithBookSetup):

    def test_book_enabled_attr(self):
        self.assert_(hasattr(self.books.get_book(TESTBOOK), 'enabled_modules'))

    def test_book_enabled_attr_after_close(self):
        self.books.close_primary_connection()
        self.books.dbcon = self.books.get_new_dbcon()
        self.books.dbroot = self.books.dbcon.root()
        self.test_book_enabled_attr()
        self.books.close_primary_connection()
        self.books.close()
    
        #self.books.zodb = ZODB.config.databaseFromURL(BOOKS_CONF)
        #self.books.dbcon = self.books.zodb.open()
        #self.books.dbroot = self.books.dbcon.root()
        #self.test_book_enabled_attr()


if __name__ == "__main__":
    main()
