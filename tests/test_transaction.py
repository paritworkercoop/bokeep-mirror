#!/usr/bin/env python2.4

from bokeep.book import BoKeepBookSet
from bokeep.book_transaction import Transaction
from bokeep.util import ends_with_commit

# from ZOPE
import transaction


books = BoKeepBookSet("test_books.conf")
if books.has_book("test_book_1"):
    test_book_1 = books.get_book("test_book_1")
else:
    test_book_1 = books.add_book("test_book_1")

class Type1Transaction(Transaction):
    def __init__(self):
        Transaction.__init__(self)
        self.reset_data()
    
    def reset_data(self):
        self.data = "blah"

    def append_data(self, append_text):
        self.data += append_text

key = test_book_1.insert_transaction( Type1Transaction() )

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
    transaction.get().commit()

simple_tests(test_book_1, key)

trans = test_book_1.get_transaction(key)
assert( trans.data == "blah shit" )



test_book_1.remove_transaction(key)


