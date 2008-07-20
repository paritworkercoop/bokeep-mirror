#!/usr/bin/env python

from bokeep.book import BoKeepBookSet
from bokeep.book_transaction import \
    Transaction, new_transaction_committing_thread, TransactionMirror
from bokeep.util import ends_with_commit

books = BoKeepBookSet("test_books.conf")
if books.has_book("test_book_1"):
    test_book_1 = books.get_book("test_book_1")
else:
    test_book_1 = books.add_book("test_book_1")

assert( test_book_1.book_name == "test_book_1" )

class Type1Transaction(Transaction):
    def __init__(self):
        Transaction.__init__(self)
        self.reset_data()
    
    def reset_data(self):
        self.data = "blah"

    def append_data(self, append_text):
        self.data += append_text

trans_key = test_book_1.insert_transaction( Type1Transaction() )

@ends_with_commit
def simple_tests(book, key):
    trans = book.get_transaction(key)
    assert( trans.data == "blah" )
    trans.data = "ha"
    assert( trans.data == "ha" )
    trans.reset_data()
    assert( trans.data == "blah" )
    trans.append_data(" shit")
    assert( trans.data == "blah shit" )

simple_tests(test_book_1, trans_key)

@ends_with_commit
def after_commit_read(book, trans_key):
    trans = book.get_transaction(trans_key)
    assert( trans.data == "blah shit" )

after_commit_read(test_book_1, trans_key)

@ends_with_commit
def use_commit_thread(trans_thread, book, trans_key):
    trans_thread.add_change_tracker_block((book.book_name, trans_key))
    trans_thread.mod_transaction_attr(
        (book.book_name, trans_key), 'data', 'fuck')
    trans_thread.remove_change_tracker((book.book_name, trans_key))
    trans_thread.add_change_tracker_block((book.book_name, trans_key))
    trans_thread.remove_change_tracker((book.book_name, trans_key))

trans_thread = new_transaction_committing_thread(books)
use_commit_thread(trans_thread, test_book_1, trans_key)

trans = test_book_1.get_transaction(trans_key)
assert( trans.data == "fuck" )

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

use_commit_thread_again(trans_thread, books, test_book_1, trans_key)

trans = test_book_1.get_transaction(trans_key)
assert( trans.data == "blah shoot" )

@ends_with_commit
def use_mirror_class(books, book, trans_key):
    trans_thread.add_change_tracker_block((book.book_name, trans_key))
    mirror = TransactionMirror( book.book_name, trans_key, trans_thread)
    mirror.data = "juice"
    mirror.append_data(" maker")
    trans_thread.remove_change_tracker((book.book_name, trans_key))
    trans_thread.add_change_tracker_block((book.book_name, trans_key))
    trans_thread.remove_change_tracker((book.book_name, trans_key))

use_mirror_class(books, test_book_1, trans_key)

trans_thread.end_thread_and_join()

trans = test_book_1.get_transaction(trans_key)
assert( trans.data == "juice maker" )

test_book_1.remove_transaction(trans_key)


