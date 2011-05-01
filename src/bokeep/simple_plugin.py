# Copyright (C) 2011  ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
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

# zodb imports
from persistent.mapping import PersistentMapping

# bokeep imports
from bokeep.prototype_plugin import PrototypePlugin

class SimplePlugin(PrototypePlugin):
    def __init__(self):
        self.trans_registry = PersistentMapping()
        self.type_strings = self.__class__.DEFAULT_TYPE_STRS

    def register_transaction(self, front_end_id, trust_trans):
        assert( not self.has_transaction(front_end_id) )
        self.trans_registry[front_end_id] = trust_trans

    def remove_transaction(self, front_end_id):
        del self.trans_registry[front_end_id]

    def has_transaction(self, trans_id):
        return trans_id in self.trans_registry

    @classmethod
    def get_transaction_type_codes(cls):
        # in python 3 range will be a generator instead of returning a tuple,
        # that is, it will behave like xrange, so we call tuple() to cover that future
        return tuple( range( len(cls.ALL_TRANSACTION_TYPES) ) )

    @classmethod
    def get_transaction_type_from_code(cls, code):
        return cls.ALL_TRANSACTION_TYPES[code]

    def get_transaction_type_pulldown_string_from_code(self, code):
        return self.type_strings[code]
