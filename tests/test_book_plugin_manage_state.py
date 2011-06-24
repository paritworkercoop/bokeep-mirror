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

# python
from unittest import TestCase, main
from os import remove
from glob import glob

# Bo-Keep
from bokeep.gui.config.state import \
    BoKeepConfigGuiState, \
    DB_ENTRY_CHANGE, DB_PATH_CHANGE, BOOK_CHANGE, BACKEND_PLUGIN_CHANGE, \
    DB_PATH, BOOKSET, BOOK

# Bo-Keep tests
from test_bokeep_book import create_tmp_filestorage_filename

class BookPluginManageStateBasicSetup(TestCase):
    def setUp(self):
        self.state = BoKeepConfigGuiState()
        self.filestorage_files = []

    def tearDown(self):
        self.state.close()
        for fs_file in self.filestorage_files:
            for file_name in glob(fs_file + '*'):
                remove(file_name)

class BookPluginManageStateTest(BookPluginManageStateBasicSetup):
    def test_filestorage_changes(self):
        for i in xrange(10):
            # the top of this loop should work the same both the first
            # time through, and all subsequent times, even though the
            # first time is very different
            self.assertFalse( self.state.action_allowed(DB_PATH_CHANGE) )
            filename = create_tmp_filestorage_filename()
            self.filestorage_files.append(filename)
            self.assert_( self.state.action_allowed(DB_ENTRY_CHANGE) )
            self.state.do_action(DB_ENTRY_CHANGE, filename)
            self.assert_( self.state.action_allowed(DB_PATH_CHANGE) )
            self.state.do_action(DB_PATH_CHANGE)
            self.assertEquals( None, self.state.db_error_msg )
            self.assertNotEquals( None, self.state.data[BOOKSET] )
            self.assert_(self.state.action_allowed(BOOK_CHANGE))

class BookPluginManageStateAfterDBSetSetup(BookPluginManageStateBasicSetup):
    def setUp(self):
        BookPluginManageStateBasicSetup.setUp(self)
        self.filename_1 = create_tmp_filestorage_filename()
        self.filestorage_files.append(self.filename_1)        
        self.state.do_action(DB_ENTRY_CHANGE, self.filename_1)
        self.state.do_action(DB_PATH_CHANGE)
    
TESTBOOK = "mr_book"
TEST_PLUG = "bokeep.plugins.trust"
class BookPluginManageStateAfterDBSetTest(BookPluginManageStateAfterDBSetSetup):
    def test_book_change_add_book(self):
        # this line is technically whitebox testing...
        self.assertFalse( self.state.data[BOOKSET].has_book(TESTBOOK) )
        self.state.book_liststore.append((TESTBOOK,))
        self.state.do_action(BOOK_CHANGE, TESTBOOK)
        # technically whitebox testing
        self.assert_( self.state.data[BOOKSET].has_book(TESTBOOK) )
        self.state.plugin_liststore.append((TEST_PLUG, False))
        self.state.do_action(BOOK_CHANGE, None)
        self.state.do_action(BOOK_CHANGE, TESTBOOK)
        # whitebox testing
        self.assert_(self.state.data[BOOKSET].get_book(
                TESTBOOK).has_disabled_frontend_plugin(TEST_PLUG) )

if __name__ == "__main__":
    main()
