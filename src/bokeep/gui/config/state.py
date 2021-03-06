# Copyright (C) 2010-2011  ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
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
#          Samuel Pauls <samuel@parit.ca>

# python imports
from os.path import \
    exists, basename, split as path_split, join as path_join, abspath
from os import makedirs

# gtk
from gtk import ListStore

# ZODB
from ZODB import DB
from ZODB.FileStorage import FileStorage
from ZODB.config import databaseFromURL

# bo-keep
from bokeep.util import FunctionAndDataDrivenStateMachine, null_function
from bokeep.config import DEFAULT_BOOKS_FILESTORAGE_FILE,\
    ZODB_CONFIG_FILESTORAGE, ZODB_CONFIG_ZCONFIG
from bokeep.book import BoKeepBookSet, BackendPluginImportError, FrontendPluginImportError

# possible actions
(DB_ENTRY_CHANGE, DB_PATH_CHANGE, BOOK_CHANGE, BACKEND_PLUGIN_CHANGE) = \
    range(4)

# tuple indexes for data stored in BoKeepConfigGuiState
(DB_PATH, DB_ACCESS_METHOD, BOOKSET, BOOK) = range(4)

class BoKeepConfigGuiState(FunctionAndDataDrivenStateMachine):
    NUM_STATES = 3
    (
        # There is no working database selected.
        NO_DATABASE,
        # There is a working database, but no book selected.
        NO_BOOK,
        # There is a book selected on a working database.
        BOOK_SELECTED,
    ) = range(NUM_STATES)

    def __init__(self, db_error_msg=None, call_for_new_plugins=null_function):
        FunctionAndDataDrivenStateMachine.__init__(
            self,
            data=(None, None, None), # DB_PATH, BOOKSET, BOOK
            initial_state=BoKeepConfigGuiState.NO_DATABASE)
        self.db_error_msg = db_error_msg
        self.book_liststore = ListStore(str)
        self.frontend_plugin_liststore = ListStore(str, bool)
        self.call_for_new_plugins = call_for_new_plugins
        self.run_until_steady_state()
        assert(self.state == BoKeepConfigGuiState.NO_DATABASE)

    def get_table(self):
        if hasattr(self, '_v_table_cache'):
            return self._v_table_cache
        
        self._v_table_cache = (
            # NO_DATABASE
            ( (BoKeepConfigGuiState.make_action_check_function(
                        DB_ENTRY_CHANGE),
              lambda selfish, next_state:
                  (selfish._v_action_arg[0], selfish._v_action_arg[1], 
                   None, None),
              BoKeepConfigGuiState.NO_DATABASE ),
             (BoKeepConfigGuiState.make_action_check_function(DB_PATH_CHANGE),
              BoKeepConfigGuiState.__open_bookset_load_list,
              BoKeepConfigGuiState.NO_BOOK ),
             ), # NO_DATABASE
              
            # NO_BOOK
            ( (lambda selfish, next_state: selfish.data[BOOKSET] == None,
               lambda selfish, next_state: selfish.data,
               BoKeepConfigGuiState.NO_DATABASE),
              (BoKeepConfigGuiState.make_action_check_function(
                        DB_ENTRY_CHANGE),
              BoKeepConfigGuiState.__clear_book_list_absorb_changed_path,
              BoKeepConfigGuiState.NO_DATABASE ),
             (BoKeepConfigGuiState.make_action_check_function(BOOK_CHANGE),
              BoKeepConfigGuiState.__handle_book_change_load_plugin_list,
              BoKeepConfigGuiState.BOOK_SELECTED),
             ), # NO_BOOK

            # BOOK_SELECTED
            ((lambda selfish, next_state: selfish.data[BOOK] == None,
              BoKeepConfigGuiState.__clear_plugin_list,
              BoKeepConfigGuiState.NO_BOOK),
             (BoKeepConfigGuiState.make_action_check_function(
                        DB_ENTRY_CHANGE),
              BoKeepConfigGuiState.__apply_plugin_changes_and_clear,
              BoKeepConfigGuiState.NO_DATABASE ),
             (BoKeepConfigGuiState.make_action_check_function(BOOK_CHANGE),
              BoKeepConfigGuiState.__apply_plugin_changes_and_reset_plugin_list,
              BoKeepConfigGuiState.BOOK_SELECTED),
             (BoKeepConfigGuiState.make_action_check_function(
                        BACKEND_PLUGIN_CHANGE),
              BoKeepConfigGuiState.__record_backend_plugin,
              BoKeepConfigGuiState.BOOK_SELECTED),
             ), # BOOK_SELECTED
            )
        
        return self._v_table_cache

    def action_allowed(self, action):
        if not hasattr(self, '_v_action_allowed_table'):
            self._v_action_allowed_table = {
                DB_ENTRY_CHANGE: lambda: True,
                DB_PATH_CHANGE: lambda:
                    self.state==BoKeepConfigGuiState.NO_DATABASE and \
                    self.data[DB_PATH] != None and \
                    self.data[DB_ACCESS_METHOD] != None,
                BOOK_CHANGE: lambda:
                    self.state != BoKeepConfigGuiState.NO_DATABASE,
                BACKEND_PLUGIN_CHANGE:
                    lambda: self.state == BoKeepConfigGuiState.BOOK_SELECTED,
                }
        if action in self._v_action_allowed_table:
            return self._v_action_allowed_table[action]()
        else:
            raise Exception("action %s is not defined" % action)

    # transition functions
    def __open_bookset_load_list(self, next_state):
        assert(self.data[DB_PATH] != None)
        assert(self.data[DB_ACCESS_METHOD] != None)
        new_path = self.data[DB_PATH]
        new_path = abspath(new_path)
        access_method = self.data[DB_ACCESS_METHOD]
        if not exists(new_path):
            directory, filename = path_split(new_path)
            if not exists(directory):
                makedirs(directory)
            if filename == '':
                new_path = path_join(directory,
                                     DEFAULT_BOOKS_FILESTORAGE_FILE)
            try:
                if access_method == ZODB_CONFIG_FILESTORAGE:
                    # Create a new file storage for transactions.
                    fs = FileStorage(new_path, create=True )
                    db = DB(fs)
                    db.close()
                elif access_method == ZODB_CONFIG_ZCONFIG:
                     # Create a new Zope configuration for transactions.
                    if new_path.endswith(".conf"):
                        file_storage_path = new_path[:-5]
                    file_storage_path += ".fs"
                    zconfig_fp = file(new_path, 'w')
                    zconfig_fp.write(
"""<zodb>
  <filestorage>
  path %s
  </filestorage>
</zodb>
""" % file_storage_path
                    )
                    zconfig_fp.close()
            except IOError, e:
                self.db_error_msg = str(e)
                return (None, None, None, None)
        try:
            db = None
            if access_method == ZODB_CONFIG_FILESTORAGE:
                db = DB(FileStorage(new_path, create=False))
            elif access_method == ZODB_CONFIG_ZCONFIG:
                db = databaseFromURL(new_path)
        except IOError, e:
            self.db_error_msg = str(e)
            return (None, None, None, None)
        else:
            self.db_error_msg = None
            bs = BoKeepBookSet(db)
            for book_name, book in bs.iterbooks():
                self.book_liststore.append((book_name,))
            return (self.data[DB_PATH], self.data[DB_ACCESS_METHOD], bs, None)

    def __load_book_list(self, next_state):
        assert(self.data[BOOKSET] != None)
        return self.data

    def __clear_book_list(self, next_state):
        self.book_liststore.clear()
        self.data[BOOKSET].close()
        return (self.data[DB_PATH], self.data[DB_ACCESS_METHOD], None, None)

    def __clear_book_list_absorb_changed_path(self, next_state):
        self.__clear_book_list(next_state)
        return (self._v_action_arg[0], self._v_action_arg[1], None, None)

    def __handle_book_change_load_plugin_list(self, next_state):
        self.frontend_plugin_liststore.clear()
        new_book_name = self._v_action_arg
        if new_book_name == None:
            return (self.data[DB_PATH], self.data[DB_ACCESS_METHOD],
                    self.data[BOOKSET], None)
        if not self.data[BOOKSET].has_book(new_book_name):
            self.data[BOOKSET].add_book(new_book_name)
        new_book = self.data[BOOKSET].get_book(new_book_name)
        # construct frontend_plugin_liststore from book
        for plugin_name in new_book.get_frontend_plugins().iterkeys():
            self.frontend_plugin_liststore.append((plugin_name, True))
        for plugin_name in new_book.disabled_modules.iterkeys():
            self.frontend_plugin_liststore.append((plugin_name, False))
        return (self.data[DB_PATH], self.data[DB_ACCESS_METHOD],
                self.data[BOOKSET], new_book )

    def __clear_plugin_list(self, next_state = None):
        self.frontend_plugin_liststore.clear()
        return self.data

    def __apply_plugin_changes_and_clear(self, next_state):
        """Sets the GUI front-end plugin list depending on the selected book.
        """
        
        modules_not_found = self.__apply_plugin_changes()
        if modules_not_found == []:
            self.__clear_plugin_list()
            return self.__clear_book_list(next_state)
        else:
            raise FrontendPluginImportError(modules_not_found)

    def __apply_plugin_changes_and_reset_plugin_list(self, next_state):
        modules_not_found = self.__apply_plugin_changes()
        if modules_not_found == []:
            return self.__handle_book_change_load_plugin_list(next_state)
        else:
            raise FrontendPluginImportError(modules_not_found)

    def __record_backend_plugin(self, next_state):
        self._v_backend_plugin = self._v_action_arg
        return self.data

    # helper functions that aren't transition functions

    def __apply_plugin_changes(self):
        not_found_modules = []
        for plugin_name, plugin_enabled in self.frontend_plugin_liststore:
            # fix any plugins that are marked enabled, but not
            if plugin_enabled and \
                    not self.data[BOOK].has_enabled_frontend_plugin(plugin_name):
                # if such a plugin isn't disabled, it has to be added
                try:
                    if not self.data[BOOK].has_disabled_frontend_plugin(plugin_name):
                        self.data[BOOK].add_frontend_plugin(plugin_name)
                    # now we can enable it
                    self.data[BOOK].enable_frontend_plugin(plugin_name)

                    # Configure the newly added frontend plugins.
                    book = self.data[BOOK]
                    FRONTEND = False
                    frontend_plugin = \
                        book.get_frontend_plugin(plugin_name)
                    self.call_for_new_plugins(book, FRONTEND, frontend_plugin)

                except FrontendPluginImportError:
                    not_found_modules.append(plugin_name)
            # fix any plugins that are marked disabled, but aren't
            elif not plugin_enabled and \
                    not self.data[BOOK].has_disabled_frontend_plugin(plugin_name):
                # such a plugin might be enabled and just need to be disabled
                if self.data[BOOK].has_enabled_frontend_plugin(plugin_name):
                    self.data[BOOK].disable_frontend_plugin(plugin_name)
                # or it may have never been added
                else:
                    try:
                        self.data[BOOK].add_frontend_plugin(plugin_name)
                    except FrontendPluginImportError:
                        not_found_modules.append(plugin_name)

        if self.data[BOOK] != None and hasattr(self, '_v_backend_plugin'):
            try:
                self.data[BOOK].set_backend_plugin(self._v_backend_plugin)
                
                # Configure the newly added backend plugin.
                book = self.data[BOOK]
                BACKEND = True
                backend_plugin = book.get_backend_plugin()
                self.call_for_new_plugins(book, BACKEND, backend_plugin)
            except BackendPluginImportError:
                not_found_modules.append(self._v_backend_plugin)
            finally:
                del self._v_backend_plugin

        return not_found_modules

    def close(self):
        if self.data[BOOKSET] != None:
            self.data[BOOKSET].close()
