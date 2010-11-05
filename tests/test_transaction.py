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
from unittest import TestCase, main
import sys
# ZODB imports
import transaction
from ZODB.FileStorage import FileStorage
from ZODB import DB

from bokeep.book import BoKeepBookSet
from bokeep.util import ends_with_commit

from test_transaction_and_module import Type1Transaction
from test_bokeep_book import BoKeepWithBookSetup, TESTBOOK

class BoKeepBasicTest(BoKeepWithBookSetup):
    def setUp(self):
        BoKeepWithBookSetup.setUp(self)        
        self.trans_key = self.test_book_1.insert_transaction(
            Type1Transaction() )
        transaction.get().commit()

    def test_interesting_sequence(self):
        self.assertEquals( self.test_book_1.book_name, TESTBOOK )

        @ends_with_commit
        def simple_tests(book, key):
            trans = book.get_transaction(key)
            self.assertEquals( trans.data, "blah" )
            trans.data = "ha"
            self.assertEquals( trans.data, "ha" )
            trans.reset_data()
            self.assertEquals( trans.data, "blah" )
            trans.append_data(" shit")
            self.assertEquals( trans.data, "blah shit" )

        simple_tests(self.test_book_1, self.trans_key)

        @ends_with_commit
        def after_commit_read(book, trans_key):
            trans = book.get_transaction(trans_key)
            self.assertEquals( trans.data, "blah shit" )

        after_commit_read(self.test_book_1, self.trans_key)

        self.test_book_1.remove_transaction(self.trans_key)
        transaction.get().commit()

if __name__ == "__main__":
    main()
