#!/usr/bin/env python

# Python library
from sys import argv

# Bo-Keep
from bokeep.config import get_database_cfg_file
from bokeep.book import BoKeepBookSet

def bokeep_main():
    bookset = BoKeepBookSet( get_database_cfg_file() )
    assert( len(argv) == 2 )
    book_name = argv[1]
    assert( not bookset.has_book(book_name) )
    bookset.add_book(book_name)
    bookset.close_primary_connection()

if __name__ == "__main__":
    bokeep_main()

