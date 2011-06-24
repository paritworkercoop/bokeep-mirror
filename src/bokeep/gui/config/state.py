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

# gtk
from gtk import ListStore

# ZODB
from ZODB import DB
from ZODB.FileStorage import FileStorage

# bo-keep
from bokeep.util import \
    ends_with_commit, FunctionAndDataDrivenStateMachine, \
    state_machine_do_nothing, state_machine_always_true
from bokeep.config import DEFAULT_BOOKS_FILESTORAGE_FILE
from bokeep.book import BoKeepBookSet, BackendPluginImportError, FrontendPluginImportError

# possible actions
(DB_ENTRY_CHANGE, DB_PATH_CHANGE, BOOK_CHANGE, BACKEND_PLUGIN_CHANGE) = \
    range(4)

# tuple indexes for data stored in BoKeepConfigGuiState
(DB_PATH, BOOKSET, BOOK) = range(3)

class BoKeepConfigGuiState(FunctionAndDataDrivenStateMachine):
    NUM_STATES = 3
    (
        # There is no working database selected
        NO_DATABASE,
        # There is a working database, but no book selected
        NO_BOOK,
        # There is a book selected on a working database
        BOOK_SELECTED,
        ) = range(NUM_STATES)

    def __init__(self, db_error_msg=None):
        FunctionAndDataDrivenStateMachine.__init__(
            self,
            data=(None, None, None), # DB_PATH, BOOKSET, BOOK
            initial_state=BoKeepConfigGuiState.NO_DATABASE)
        self.db_error_msg = db_error_msg
        self.book_liststore = ListStore(str)
        self.plugin_liststore = ListStore(str, bool)
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
                  (selfish._v_action_arg, None, None),
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
                    self.data[DB_PATH] != None,
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
        new_path = self.data[DB_PATH]
        new_path = abspath(new_path)
        if not exists(new_path):
            directory, filename = path_split(new_path)
            if not exists(directory):
                makedirs(directory)
            if filename == '':
                new_path = path_join(directory,
                                     DEFAULT_BOOKS_FILESTORAGE_FILE)
            try:
                fs = FileStorage(new_path, create=True )
                db = DB(fs)
                db.close()
            except IOError, e:
                self.db_error_msg = str(e)
                return (None, None, None)
        try:
            fs = FileStorage(new_path, create=False )
            db = DB(fs)
        except IOError, e:
            self.db_error_msg = str(e)
            return (None, None, None)
        else:
            self.db_error_msg = None
            bs = BoKeepBookSet(db)
            for book_name, book in bs.iterbooks():
                self.book_liststore.append((book_name,))
            return (self.data[DB_PATH], bs, None)

    def __load_book_list(self, next_state):
        assert(self.data[BOOKSET] != None)
        return self.data

    def __clear_book_list(self, next_state):
        self.book_liststore.clear()
        self.data[BOOKSET].close()
        return (self.data[DB_PATH], None, None)

    def __clear_book_list_absorb_changed_path(self, next_state):
        self.__clear_book_list(next_state)
        return (self._v_action_arg, None, None)

    def __handle_book_change_load_plugin_list(self, next_state):
        self.plugin_liststore.clear()
        new_book_name = self._v_action_arg
        if new_book_name == None:
            return (self.data[DB_PATH], self.data[BOOKSET], None)
        if not self.data[BOOKSET].has_book(new_book_name):
            self.data[BOOKSET].add_book(new_book_name)
        new_book = self.data[BOOKSET].get_book(new_book_name)
        # construct plugin_liststore from book
        for plugin_name in new_book.get_frontend_plugins().iterkeys():
            self.plugin_liststore.append((plugin_name, True))
        for plugin_name in new_book.disabled_frontend_plugins.iterkeys():
            self.plugin_liststore.append((plugin_name, False))
        return (self.data[DB_PATH], self.data[BOOKSET], new_book )

    def __clear_plugin_list(self, next_state):
        self.plugin_liststore.clear()
        return self.data

    def __apply_plugin_changes_and_clear(self, next_state):
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
        for plugin_name, plugin_enabled in self.plugin_liststore:
            # fix any plugins that are marked enabled, but not
            if plugin_enabled and \
                    not self.data[BOOK].has_enabled_frontend_plugin(plugin_name):
                # if such a plugin isn't disabled, it has to be added
                try:
                    if not self.data[BOOK].has_disabled_frontend_plugin(plugin_name):
                        self.data[BOOK].add_frontend_plugin(plugin_name)
                    # now we can enable it
                    self.data[BOOK].enable_frontend_plugin(plugin_name)
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
            except BackendPluginImportError:
                not_found_modules.append(self._v_backend_plugin)
            finally:
                del self._v_backend_plugin

        return not_found_modules

    def close(self):
        if self.data[BOOKSET] != None:
            self.data[BOOKSET].close()
