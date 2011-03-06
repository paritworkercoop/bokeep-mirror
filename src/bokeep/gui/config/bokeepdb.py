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
# Authors: Mark Jenkins <mark@parit.ca>
#          Sara Arenson <sara_arenson@yahoo.ca>

# python imports
from os.path import \
    exists, isdir, isfile, basename, split as path_split, join as path_join, abspath
import os
from os import makedirs
import sys

# ZODB imports
from ZODB.FileStorage import FileStorage
from ZODB import DB
import transaction

# gtk imports
from gtk import \
    ListStore, \
    TreeView, TreeViewColumn, CellRendererText, CellRendererToggle, \
    RESPONSE_OK, RESPONSE_CANCEL, RESPONSE_DELETE_EVENT, \
    FILE_CHOOSER_ACTION_SAVE, FileChooserDialog, \
    STOCK_CANCEL, STOCK_SAVE

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

def establish_bokeep_db(mainwindow, config_path, db_exception):
    assert(db_exception == None or
           isinstance(db_exception, BoKeepConfigurationDatabaseException))
    if db_exception == None:
        extra_error_info = None
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
            result==RESPONSE_DELETE_EVENT )
    if new_filestorage_path == None or result!=RESPONSE_OK:
        return None

    # should save new_filestorage_path in config if different
    if new_filestorage_path != filestorage_path:
        config.set(ZODB_CONFIG_SECTION, ZODB_CONFIG_FILESTORAGE,
                   filestorage_path)
        config_fp = file(config_path, 'w')
        config.write(config_fp)
        config_fp.close()

    fs = FileStorage(filestorage_path, create=False )
    return BoKeepBookSet( DB(fs) )    

def available_plugins(plugin_file_name):
    """Returns a list of plugins, automatically detected.

Searches all directories in python path, plus /bokeep/plugins in each of these 
directories.

A module [name].py is a plugin if there's a corresponding file called [name]_[plugin_file_name] in the same directory, e.g. [name]_BOKEEP_PLUGIN if plugin_file_name=BOKEEP_PLUGIN.

A package is a plugin if there's a [plugin_file_name] file in its base directory.  e.g.
package name payroll has directory payroll/, plugin_file_name=BOKEEP_PLUGIN, and file payroll/BOKEEP_PLUGIN exists.

The [plugin_file_name] files are empty - created with touch.
    """
    dir_list = [ directory 
                 for directory in sys.path
                 if exists(directory) ]
    dir_list.extend([ path_join(directory, "bokeep", "plugins") 
                      for directory in dir_list
                      if exists(path_join(directory, "bokeep", "plugins")) ])

    bokeep_packages = []
    bokeep_modules = []

    for directory in dir_list:
        items = set(os.listdir(directory))
        sub_directories = set([ item
                                for item in items 
                                if isdir(path_join(directory, item)) ])

        new_packages = [ sub_dir
                         for sub_dir in sub_directories
                         if exists( 
                             path_join(directory, sub_dir, plugin_file_name)) ]     
        
        module_names = [ item[0:item.index("_"+plugin_file_name)]
                         for item in items.difference(sub_directories)
                         if item.endswith("_"+plugin_file_name) ]

        new_modules = [ module_name 
                        for module_name in module_names
                        if exists( path_join(directory, module_name+".py") ) ]

        if directory.endswith(path_join("bokeep", "plugins")):
            new_packages = [ "bokeep.plugins." + name for name in new_packages]
            new_modules = [ "bokeep.plugins." + name for name in new_modules]

        bokeep_packages.extend(new_packages)
        bokeep_modules.extend(new_modules)

    return bokeep_packages + bokeep_modules

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
        self.books_window.add(self.books_tv)
        self.books_tv.show()
        self.plugins_tv = TreeView(self.state.plugin_liststore)
        self.plugins_tv.append_column(
            TreeViewColumn("Plugin", CellRendererText(), text=0) )
        crt = CellRendererToggle()
        crt.set_radio(False)
        self.plugins_tv.append_column(
            TreeViewColumn("Enabled", crt, active=1) )
        self.plugins_window.add(self.plugins_tv)
        self.plugins_tv.show()
        available_plugin_liststore = ListStore(str)
        for plugin_name in available_plugins("BOKEEP_PLUGIN"):
            available_plugin_liststore.append([plugin_name])
        self.plugin_add_entry_combo.set_model(available_plugin_liststore)
        self.plugin_add_entry_combo.set_text_column(0)
        if filestorage_path != None:
            self.state.do_action(DB_ENTRY_CHANGE, filestorage_path)
            self.state.do_action(DB_PATH_CHANGE)
        self.last_commit_db_path = filestorage_path

        if error_msg == None:
            error_msg = ""
        self.message_label.set_label(error_msg)
        self.path_entry_lock = True
        self.db_path_entry.set_text(filestorage_path)
        self.path_entry_lock = False

        self.set_sensitivities()
        self.selection_change_lock = False
        self.backend_entry_lock = False

    def run(self):
        return_value = self.bokeep_config_dialog.run()
        if self.state.action_allowed(BOOK_CHANGE):
            self.state.do_action(BOOK_CHANGE, None)
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
            (self.book_add_button, BOOK_CHANGE),
            (self.plugins_tv, BACKEND_PLUGIN_CHANGE),
            (self.plugin_add_entry_combo, BACKEND_PLUGIN_CHANGE),
            (self.plugin_add_button, BACKEND_PLUGIN_CHANGE),
            (self.backend_plugin_entry, BACKEND_PLUGIN_CHANGE),
            ):
            obj.set_sensitive( self.state.action_allowed(action) )

    def get_currently_selected_book(self, *args):
        sel = self.books_tv.get_selection()
        sel_iter = sel.get_selected()[1]
        if sel_iter == None:
            return None
        else:
            sel_row = self.state.book_liststore[sel_iter]
            return sel_row[0]

    # event handles

    def on_apply_db_change_button_clicked(self, *args):
        self.last_commit_db_path = self.db_path_entry.get_text()
        self.selection_change_lock = True
        self.state.do_action(DB_PATH_CHANGE)
        self.selection_change_lock = False
        self.set_sensitivities()

    def on_selectdb_button_clicked(self, *args):
        fcd = FileChooserDialog(
            "Where should the database be?",
            self.bokeep_config_dialog,
            FILE_CHOOSER_ACTION_SAVE,
            (STOCK_CANCEL, RESPONSE_CANCEL, STOCK_SAVE, RESPONSE_OK) )
        fcd.set_modal(True)
        result = fcd.run()
        filestorage_path = fcd.get_filename()
        fcd.destroy()
        if result == RESPONSE_OK and filestorage_path != None:
            self.path_entry_lock = True
            self.db_path_entry.set_text(filestorage_path)
            self.path_entry_lock = False
            self.selection_change_lock = True
            self.state.do_action(DB_ENTRY_CHANGE,
                                 filestorage_path)
            self.state.do_action(DB_PATH_CHANGE)
            self.selection_change_lock = False
            self.last_commit_db_path = filestorage_path
            self.set_sensitivities()            

    def on_db_path_entry_changed(self, *args):
        if not self.path_entry_lock:
            filestorage_path = self.db_path_entry.get_text()
            self.selection_change_lock = True
            self.state.do_action(DB_ENTRY_CHANGE, filestorage_path)
            self.selection_change_lock = False
            self.set_sensitivities()

    def on_book_add_entry_clicked(self, *args):
        self.books_tv.get_selection().unselect_all()
        self.selection_change_lock = True
        self.state.do_action(BOOK_CHANGE, None)
        self.selection_change_lock = False
        self.set_sensitivities()

    def on_book_add_clicked(self, *args):
        new_book = self.book_add_entry.get_text()
        self.state.book_liststore.append( (new_book,))
        self.book_add_entry.set_text("")
        cur_book = self.get_currently_selected_book()
        # this ensures the book get added
        self.state.do_action(BOOK_CHANGE, new_book)
        self.state.do_action(BOOK_CHANGE, cur_book)

    def on_plugin_add_clicked(self, *args):
        entry = self.plugin_add_entry_combo.child
        self.state.plugin_liststore.append((entry.get_text(), True))
        entry.set_text("")

    def on_backend_plugin_entry_changed(self, *args):
        if not self.backend_entry_lock:
            self.state.do_action(
                BACKEND_PLUGIN_CHANGE, self.backend_plugin_entry.get_text())

    def on_book_selection_change(self, *args):
        if not self.selection_change_lock:
            sel_book = self.get_currently_selected_book()
            if sel_book == None:
                self.state.do_action(BOOK_CHANGE, None)
                self.backend_entry_lock = True
                self.backend_plugin_entry.set_text("")
                self.backend_entry_lock = False
            else:
                self.state.do_action(BOOK_CHANGE, sel_book)
                self.backend_entry_lock = True
                self.backend_plugin_entry.set_text(
                    self.state.data[BOOK].get_backend_module_name() )
                self.backend_entry_lock = False
            self.set_sensitivities()
            
