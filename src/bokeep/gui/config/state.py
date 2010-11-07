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

# bo-keep
from bokeep.util import \
    ends_with_commit, FunctionAndDataDrivenStateMachine, \
    state_machine_do_nothing, state_machine_always_true
from bokeep.config import DEFAULT_BOOKS_FILESTORAGE_FILE

# possible actions
(DB_ENTRY_CHANGE, DB_PATH_CHANGE, BOOK_CHANGE, BACKEND_PLUGIN_CHANGE) = \
    range(4)

# tuple indexes for data stored in BoKeepConfigGuiState
(DB_PATH, DB_HANDLE, BOOK) = range(3)

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

    def __init__(self, db_error_msg=""):
        FunctionAndDataDrivenStateMachine.__init__(
            self,
            data=("", None, None), # DB_PATH, DB_HANDLE, BOOK
            initial_state=BoKeepGuiState.NO_DATABASE)
        self.db_error_msg = db_error_msg
        self.book_liststore = ListStore()
        self.plugin_liststore = ListStore()
        self.run_until_steady_state()
        assert(self.state == BoKeepGuiState.NO_DATABASE)

    def get_table(self):
        if hasattr(self, '_v_table_cache'):
            return self._v_table_cache
        
        self._v_table_cache = (
            # NO_DATABASE
            ((BoKeepConfigGuiState.__db_path_useable,
              BoKeepConfigGuiState.__load_book_list,
              BoKeepConfigGuiState.NO_BOOK),
             (BoKeepConfigGuiState.__make_action_check_function(DB_PATH_CHANGE),
              BoKeepConfigGuiState.__absorb_changed_db_path,
              BoKeepConfigGuiState.NO_DATABASE ),
             ), # NO_DATABASE
              
            # NO_BOOK
            ((BoKeepConfigGuiState.__make_action_check_function(
                        DB_ENTRY_CHANGE),
              BoKeepConfigGuiState.__clear_book_list,
              BoKeepConfigGuiState.NO_DATABASE ),
             (BoKeepConfigGuiState.__make_action_check_function(
                            DB_PATH_CHANGE),
               BoKeepConfigGuiState.__clear_book_list,
               BoKeepConfigGuiState.NO_DATABASE ),
             (BoKeepConfigGuiState.__make_action_check_function(BOOK_CHANGE),
              BoKeepConfigGuiState.__set_plugin_list,
              BoKeepConfigGuiState.BOOK_SELECTED),
             ), # NO_BOOK

            # BOOK_SELECTED
            ((BoKeepConfigGuiState.__null_book_selected,
              BoKeepConfigGuiState.__clear_plugin_list,
              BoKeepConfigGuiState.NO_BOOK),
             (BoKeepConfigGuiState.__make_action_check_function(
                        DB_ENTRY_CHANGE),
              BoKeepConfigGuiState.__clear_book_and_plugin_list,
              BoKeepConfigGuiState.NO_DATABASE ),
             (BoKeepConfigGuiState.__make_action_check_function(
                            DB_PATH_CHANGE),
               BoKeepConfigGuiState.__absorb_path_clear_book_and_plugin_list,
               BoKeepConfigGuiState.NO_DATABASE ),
             (BoKeepConfigGuiState.__make_action_check_function(BOOK_CHANGE),
              BoKeepConfigGuiState.__apply_plugin_changes_and_reset_plugin_list,
              BoKeepConfigGuiState.BOOK_SELECTED),
             (BoKeepConfigGuiState.__make_action_check_function(
                        BACKEND_PLUGIN_CHANGE),
              BoKeepConfigGuiState.__record_backend_plugin,
              BoKeepConfigGuiState.BOOK_SELECTED),
             ), # BOOK_SELECTED
            )
        
        return self._v_table_cache

    
    def action_allowed(self, action):
        if not hasattr(self, '_v_action_allowed_table'):
            self._v_action_allowed_table = {
                DB_ENTRY_CHANGE: lambda True,
                DB_PATH_CHANGE: lambda True,
                BOOK_CHANGE: self.state != BoKeepConfigGuiState.NO_DATABASE,
                BACKEND_PLUGIN_CHANGE:
                    self.state == BoKeepConfigGuiState.BOOK_SELECTED,
                }
        if action in self._v_action_allowed_table:
            return self._v_action_allowed_table[action]()
        else:
            raise Exception("action %s is not defined" % action)

    # transition test functions

    def __db_path_useable(self, next_state):
        if self.data[DB_PATH] != '':
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
                    return False
            try:
                fs = FileStorage(new_path, create=False )
                db = DB(fs)
                db.close()
            except IOError, e:
                self.db_error_msg = str(e)
                return False
            else:
                return True
        return False

    def __null_book_selected(self, next_state):
        return self.data[BOOK] != None

    # transition functions

    def __load_book_list(self, next_state):
        db_handle = Db(FileStorage(self.data[DB_PATH], create=False ))
        return (self.data[DB_PATH], db_handle, self.data[BOOK])

    def __absorb_changed_db_path(self, next_state):
        return (self._v_action_arg, self.data[DB_HANDLE], self.data[BOOK]) 

    def __clear_book_list(self, next_state):
        self.book_liststore.clear()
        return (self.data[DB_PATH], self.data[DB_HANDLE], None)

    def __set_plugin_list(self, next_state):
        self.plugin_liststore.clear()
        new_book_name = self._v_action_arg
        new_book = BoKeepBookSet(self.DB_HANDLE).get_book(new_book_name)
        # construct plugin_liststore from book
        return (self.data[DB_PATH], self.data[DB_HANDLE], new_book )

    def __clear_plugin_list(self, next_state):
        self.plugin_liststore.clear()
        return self.data

    def __absorb_path_clear_book_and_plugin_list(self, next_state):
        return self.data

    def __clear_book_and_plugin_list(self, next_state):
        self.__clear_plugin_list()
        return self.__clear_book_list()

    def __apply_plugin_changes_and_reset_plugin_list(self, next_state):
        return self.data

    def __record_backend_plugin(self, next_state):
        return self.data
    
