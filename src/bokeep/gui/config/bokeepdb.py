# Copyright (C) 2010  ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
#
# This file is part of Bo-Keep.
#
# Bo-Keep is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Mark Jenkins <mark@parit.ca>

# python imports
from os.path import \
    exists, basename, split as path_split, join as path_join
from os import mkdir

# bokeep imports
from bokeep.config import \
    BoKeepConfigurationDatbaseException, get_bokeep_configuration, \
    DEFAULT_BOOKS_FILESTORAGE_FILE

def do_new_book(bookset):
    newbookname = raw_input("What is the new book called?\n"
                            "(hit with nothing to cancel)\n> ")
    if newbookname != '':
        bookset.add_book(newbookname)
    # actual gui should prevent duplicate book names
    print "\n"

def do_remove_book(bookset):
    newbookname = raw_input("What is the book being removed called?\n"
                            "(hit with nothing to cancel)\n> ")
    if newbookname != '' and bookset.has_book(newbookname)
        bookset.remove_book(newbookname)
    print "\n"    

def do_change_book(bookset):
    newbookname = raw_input("What is the book being changed called?\n"
                            "(hit with nothing to cancel)\n> ")
    if newbookname != '' and bookset.has_book(newbookname):
        print "change", newbookname
    print "\n"

def do_list_books(bookset):
    print "\n".join(name for name, book in bookset.iterbooks() )
    print "\n"

def manage_available_books(bookset):
    while True:
        option = raw_input("Manage your books, "
                           "New (N/n), Delete (D/d), Change (C/c), "
                           "List (L/l) Quit (Q/q)\n> " )
        if option in "Nn":
            do_new_book(bookset)
        elif option in "Dd":
            do_remove_book(bookset)
        elif option in "Cc":
            do_change_book(bookset)
        elif option in "Ll":
            do_list_books(bookset)
        elif option in "Qq":
            break

def establish_bokeep_db(config_path, db_exception):
    assert(db_exception == None or
           isinstance(db_exception, BoKeepConfigurationDatbaseException))
    if db_exception != None:
        print db_exception.message
        print "BoKeep requires a working database to operate"
        config = get_bokeep_configuration(config_path)
        filestorage_path = config.get(ZODB_CONFIG_SECTION,
                                      ZODB_CONFIG_FILESTORAGE)
        new_path = raw_input(
            "Where should the database be located?\n"
            "default: %s\n> " % config_path)
        if new_path == '':
            new_path = config_path
        new_path = abspath(new_path)
        if not exists(new_path):
            directory, filename = split_path(new_path)
            if not exists(directory):
                makedirs(directory)
            # the user is welcome to just specify a directory without
            # a file, and we'll use the default filestorage filename
            if filename == '':
                new_path = path_join(directory,
                                     DEFAULT_BOOKS_FILESTORAGE_FILE)
            try:
                fs = FileStorage(new_path, create=True )
                db = DB(fs)
                db.close()
            except IOError, e:
                print "there was a problem creating the database", \
                    new_path, e.message
                return None        
        try:
            fs = FileStorage(new_path, create=False )
            return BoKeepBookSet( DB(fs) )
        except IOError, e:
            pass

    return None
