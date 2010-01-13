from unittest import TestCase, main

from bokeep.book import BoKeepBookSet
from bokeep.book_transaction import \
    Transaction, new_transaction_committing_thread, TransactionMirror
from bokeep.util import ends_with_commit

class Type1Transaction(Transaction):
    def __init__(self):
        Transaction.__init__(self)
        self.reset_data()
    
    def reset_data(self):
        self.data = "blah"

    def append_data(self, append_text):
        self.data += append_text

class BoKeepBasicTest(TestCase):
    def setUp(self):
        self.books = BoKeepBookSet("tests/test_books.conf")
        if self.books.has_book("test_book_1"):
            self.test_book_1 = self.books.get_book("test_book_1")
        else:
            self.test_book_1 = self.books.add_book("test_book_1")

        self.trans_key = self.test_book_1.insert_transaction(
            Type1Transaction() )

    def test_interesting_sequence(self):
        self.assertEquals( self.test_book_1.book_name, "test_book_1" )

        @ends_with_commit
        def simple_tests(book, key):
            trans = book.get_transaction(key)
            self.assertEquals( trans.data, "blah" )
            trans.data = "ha"
            self.assertEquals( trans.data, "ha" )
            trans.reset_data()
            self.assertEquals( trans.data, "blah" )
            trans.append_data(" shit")
            self.assertEquals( trans.data, "blah shit" )

        simple_tests(self.test_book_1, self.trans_key)

        @ends_with_commit
        def after_commit_read(book, trans_key):
            trans = book.get_transaction(trans_key)
            self.assertEquals( trans.data, "blah shit" )

        after_commit_read(self.test_book_1, self.trans_key)

        @ends_with_commit
        def use_commit_thread(trans_thread, book, trans_key):
            trans_thread.add_change_tracker_block((book.book_name, trans_key))
            trans_thread.mod_transaction_attr(
                (book.book_name, trans_key), 'data', 'fuck')
            trans_thread.remove_change_tracker((book.book_name, trans_key))
            trans_thread.add_change_tracker_block((book.book_name, trans_key))
            trans_thread.remove_change_tracker((book.book_name, trans_key))
            
        trans_thread = new_transaction_committing_thread(self.books)
        use_commit_thread(trans_thread, self.test_book_1, self.trans_key)

        trans = self.test_book_1.get_transaction(self.trans_key)
        self.assertEquals( trans.data, "fuck" )

        @ends_with_commit
        def use_commit_thread_again(trans_thread, books, book, trans_key):
            trans_thread.add_change_tracker_block((book.book_name, trans_key))
            trans_thread.mod_transaction_with_func(
                (book.book_name, trans_key), 'reset_data', (), {} )
            trans_thread.mod_transaction_with_func(
                (book.book_name, trans_key), 'append_data',
                (' shoot',), {} )
            trans_thread.remove_change_tracker((book.book_name, trans_key))
            trans_thread.add_change_tracker_block((book.book_name, trans_key))
            trans_thread.remove_change_tracker((book.book_name, trans_key))
            
        use_commit_thread_again(self.trans_thread, self.books,
                                self.test_book_1, trans_key)

        trans = self.test_book_1.get_transaction(self.trans_key)
        self.assertEquals( trans.data, "blah shoot" )

        @ends_with_commit
        def use_mirror_class(books, book, trans_key):
            trans_thread.add_change_tracker_block((book.book_name, trans_key))
            mirror = TransactionMirror( book.book_name, trans_key, trans_thread)
            mirror.data = "juice"
            mirror.append_data(" maker")
            trans_thread.remove_change_tracker((book.book_name, trans_key))
            trans_thread.add_change_tracker_block((book.book_name, trans_key))
            trans_thread.remove_change_tracker((book.book_name, trans_key))

        use_mirror_class(self.books, self.test_book_1, self.trans_key)

        trans_thread.end_thread_and_join()

        trans = self.test_book_1.get_transaction(self.trans_key)
        self.assertEquals( trans.data, "juice maker" )
        self.test_book_1.remove_transaction(self.trans_key)
