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
from bokeep.book_transaction import Transaction

class Type1Transaction(Transaction):
    def __init__(self, module):
        Transaction.__init__(self)
        self.reset_data()
    
    def reset_data(self):
        self.data = "blah"

    def append_data(self, append_text):
        self.data += append_text

class Type2Transaction(Type1Transaction): pass

TYPE1, TYPE2 = range(2)

trust_transaction_types = {
    TYPE1: Type1Transaction,
    TYPE2: Type2Transaction,
}

class TestModule(object):
    def __init__(self):
        self.transaction_track_database = {}
        
    def register_transaction(self, front_end_id, trust_trans):
        self.transaction_track_database[front_end_id] = trust_trans

    def remove_transaction(self, front_end_id):
        del self.transaction_track_database[front_end_id]

    def has_transaction(self, front_end_id):
        return front_end_id in self.transaction_track_database

    @staticmethod
    def get_transaction_type_codes():
        return trust_transaction_types.keys()

    @staticmethod
    def get_transaction_type_from_code(code):
        return trust_transaction_types[code]

    @staticmethod
    def get_transaction_code_from_type(ty):
        for entry in trust_transaction_types:
            if trust_transaction_types[entry] == ty:
                return entry

        return None

    @staticmethod
    def get_transaction_type_pulldown_string_from_code(code):
        return "cool test trasnaction"
        
    @staticmethod
    def get_transaction_edit_interface_hook_from_code(code):
        return lambda: None

    @staticmethod
    def get_transaction_view_interface_hook_from_code(code):
        return lambda: None

    @staticmethod
    def get_transaction_edit_interface_hook_from_type(ty):
        return lambda: None

    @staticmethod
    def get_transaction_view_interface_hook_from_type(ty):
        return lambda: None

def get_module_class():
    return TestModule


