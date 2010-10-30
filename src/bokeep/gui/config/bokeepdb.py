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
    exists, basename, split as path_split, join as path_join, abspath
from os import makedirs

# ZODB imports
from ZODB.FileStorage import FileStorage
from ZODB import DB

# bokeep imports
from bokeep.config import \
    BoKeepConfigurationDatabaseException, get_bokeep_configuration, \
    DEFAULT_BOOKS_FILESTORAGE_FILE, ZODB_CONFIG_SECTION, \
    ZODB_CONFIG_FILESTORAGE
from bokeep.book import BoKeepBookSet

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
    if newbookname != '' and bookset.has_book(newbookname):
        bookset.remove_book(newbookname)
    print "\n"    

def do_plugin_add(book):
    new_plugin = raw_input("Name of new plugin, blank to cancel\n> ")
    if new_plugin == '': return
    book.add_module(new_plugin)

def do_plugin_config(book):
    plugin_name = raw_input("Name of new plugin, blank to cancel\n> ")
    if plugin_name == '': return
    book.get_module(plugin_name).do_config()

def do_plugin_enable(book):
    plugin_name = raw_input("Name of plugin, blank to cancel\n> ")
    if plugin_name == '': return
    book.enable_module(plugin_name)

def do_plugin_disable(book):
    plugin_name = raw_input("Name of plugin, blank to cancel\n> ")
    if plugin_name == '': return
    book.disable_plugin(plugin_name)

def do_set_backend_plugin(book):
    plugin_name = raw_input("Name of backend plugin, blank to cancel\n> ")
    if plugin_name == '': return
    book.set_backend_module(plugin_name)

def do_backend_plugin_config(book):
    book.get_backend_module().do_config()

def do_plugin_listing(book):
    print "enabled modules"
    print "\n".join(sorted(book.enabled_modules.iterkeys()))
    print 
    print "disabled modules"
    print "\n".join(sorted(book.disabled_modules.iterkeys()))
    print

    print "backend module:", book.get_backend_module()

def do_change_book(bookset):
    newbookname = raw_input("What is the book being changed called?\n"
                            "(hit with nothing to cancel)\n> ")
    if newbookname != '' and bookset.has_book(newbookname):
        book = bookset.get_book(newbookname)
        task = raw_input("Add plugin (A/a), Config plugin (C/c), "
                         "Enable plugin (E/e), Disable plugin (D/d), "
                         "Set backend plugin (S/s), "
                         "Backend plugin config (B/b), "
                         "Plugin listing (L/l), "
                         "blank for no action\n> ")
        if task in "Aa":
            do_plugin_add(book)
        elif task in "Cc":
            do_plugin_config(book)
        elif task in "Ee":
            do_plugin_enable(book)
        elif task in "Dd":
            do_plugin_disable(book)
        elif task in "Ss":
            do_set_backend_plugin(book)
        elif task in "Bb":
            do_backend_plugin_config(book)
        elif task in "Ll":
            do_plugin_listing(book)
        else:
            return
    print "\n"

def do_list_books(bookset):
    print "\n".join(name for name, book in bookset.iterbooks() )
    print "\n"

def manage_available_books(mainwindow, bookset):
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

def establish_bokeep_db(mainwindow, config_path, db_exception):
    assert(db_exception == None or
           isinstance(db_exception, BoKeepConfigurationDatabaseException))
    if db_exception != None:
        print db_exception.message
        print "BoKeep requires a working database to operate"
    
    config = get_bokeep_configuration(config_path)
    filestorage_path = config.get(ZODB_CONFIG_SECTION,
                                  ZODB_CONFIG_FILESTORAGE)
    new_path = raw_input(
        "Where should the database be located?\n"
        "default: %s\n> " % filestorage_path)
    if new_path == '':
        new_path = filestorage_path
    new_path = abspath(new_path)
    if not exists(new_path):
        directory, filename = path_split(new_path)
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
