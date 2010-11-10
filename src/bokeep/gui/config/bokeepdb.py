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
import sys

# ZODB imports
from ZODB.FileStorage import FileStorage
from ZODB import DB
import transaction

# gtk imports
from gtk import \
    TreeView, TreeViewColumn, CellRendererText, CellRendererToggle, \
    RESPONSE_OK, RESPONSE_CANCEL, RESPONSE_CLOSE

# bokeep imports
from bokeep.config import \
    BoKeepConfigurationDatabaseException, get_bokeep_configuration, \
    DEFAULT_BOOKS_FILESTORAGE_FILE, ZODB_CONFIG_SECTION, \
    ZODB_CONFIG_FILESTORAGE
from bokeep.book import BoKeepBookSet
from bokeep.gui.main_window_glade import get_main_window_glade_file
from bokeep.gui.gladesupport.glade_util import \
    load_glade_file_get_widgets_and_connect_signals

# bokeep.gui.config imports
from state import BoKeepConfigGuiState, \
    DB_ENTRY_CHANGE, DB_PATH_CHANGE, BOOK_CHANGE, BACKEND_PLUGIN_CHANGE, \
    BOOK

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
    # argument is for parent window, None right now, but this will actually
    # be something once bokeepdb.py becomes a real gui
    book.get_module(plugin_name).do_config(None)

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
    if db_exception == None:
        extra_error_info = ""
    else:
        extra_error_info = "%s\n%s" %(
            str(db_exception), 
            "BoKeep requires a working database to operate" )
    
    config = get_bokeep_configuration(config_path)
    filestorage_path = config.get(ZODB_CONFIG_SECTION,
                                  ZODB_CONFIG_FILESTORAGE)
    config_dialog = BoKeepConfigDialog(filestorage_path, extra_error_info)
    result, new_filestorage_path = config_dialog.run()
    
    assert( result == RESPONSE_OK or result==RESPONSE_CANCEL or
            result==RESPONSE_CLOSE )
    if new_filestorage_path == None or result!=RESPONSE_OK:
        return None

    # should save new_filestorage_path in config if different
    if new_filestorage_path != filestorage_path:
        config.set(ZODB_CONFIG_SECTION, ZODB_CONFIG_FILESTORAGE)
        config_fp = file(config_path, 'w')
        config.write(config_fp)
        config_fp.close()

    fs = FileStorage(filestorage_path, create=False )
    return BoKeepBookSet( DB(fs) )    

class BoKeepConfigDialog(object):
    def __init__(self, filestorage_path, error_msg=None):
        load_glade_file_get_widgets_and_connect_signals(
            get_main_window_glade_file(), "bokeep_config_dialog",
            self, self)
        self.selection_change_lock = True

        self.state = BoKeepConfigGuiState(error_msg)
        self.books_tv = TreeView(self.state.book_liststore)
        self.books_tv.append_column(
                TreeViewColumn("Book", CellRendererText(), text=0 ) )
        self.books_tv.get_selection().connect(
            "changed", self.on_book_selection_change)
        self.booksvbox.pack_start(self.books_tv)
        self.books_tv.show()
        self.plugins_tv = TreeView(self.state.plugin_liststore)
        self.plugins_tv.append_column(
            TreeViewColumn("Plugin", CellRendererText(), text=0) )
        crt = CellRendererToggle()
        crt.set_radio(False)
        self.plugins_tv.append_column(
            TreeViewColumn("Enabled", crt, active=1) )
        self.pluginsvbox.pack_start(self.plugins_tv)
        self.plugins_tv.show()
        if filestorage_path != None:
            self.state.do_action(DB_ENTRY_CHANGE, filestorage_path)
            self.state.do_action(DB_PATH_CHANGE)
        self.last_commit_db_path = filestorage_path

        if error_msg == None:
            error_msg = ""
        self.message_label.set_label(error_msg)
        self.db_path_entry.set_text(filestorage_path)

        self.set_sensitivities()
        self.selection_change_lock = False
        self.backend_entry_lock = False

    def run(self):
        return_value = self.bokeep_config_dialog.run()
        if return_value == RESPONSE_OK:
            transaction.get().commit()
        else:
            transaction.get().abort()
        self.state.close()
        self.bokeep_config_dialog.destroy()

        return return_value, self.last_commit_db_path 

    def set_sensitivities(self):
        for obj, action in (
            (self.apply_db_change_button, DB_PATH_CHANGE),
            (self.books_tv, BOOK_CHANGE),
            (self.book_add_entry, BOOK_CHANGE),
            (self.button2, BOOK_CHANGE),
            (self.plugins_tv, BACKEND_PLUGIN_CHANGE),
            (self.plugin_add_entry, BACKEND_PLUGIN_CHANGE),
            (self.button3, BACKEND_PLUGIN_CHANGE),
            (self.backend_pugin_entry, BACKEND_PLUGIN_CHANGE),
            ):
            obj.set_sensitive( self.state.action_allowed(action) )

    def on_apply_db_change_button_clicked(self, *args):
        pass

    def on_selectdb_button_clicked(self, *args):
        pass

    def on_db_path_entry_changed(self, *args):
        pass

    def on_bookadd_clicked(self, *args):
        self.state.book_liststore.append( (self.book_add_entry.get_text(),))
        self.book_add_entry.set_text("")

    def on_plugin_add_clicked(self, *args):
        self.state.plugin_liststore.append(
            (self.plugin_add_entry.get_text(), True))
        self.plugin_add_entry.set_text("")

    def on_backend_pugin_entry_changed(self, *args):
        if not self.backend_entry_lock:
            pass

    def on_book_selection_change(self, *args):
        if not self.selection_change_lock:
            sel = self.books_tv.get_selection()
            sel_iter = sel.get_selected()[1]
            if sel_iter == None:
                self.state.do_action(BOOK_CHANGE, None)
                self.backend_entry_lock = True
                self.backend_pugin_entry.set_text("")
                self.backend_entry_lock = False
            else:
                sel_row = self.state.book_liststore[sel_iter]
                book_selected = sel_row[0]
                self.state.do_action(BOOK_CHANGE, book_selected)
                self.backend_entry_lock = True
                self.backend_pugin_entry.set_text("blah")
                # backend plugins need to be able to identify themselves
                    #self.state.data[BOOK].get_backend_module().__file__)
                self.backend_entry_lock = False
            self.set_sensitivities()
            

