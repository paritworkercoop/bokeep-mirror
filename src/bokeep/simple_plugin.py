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
# Authors: Mark Jenkins <mark@parit.ca>
#          Samuel Pauls <samuel@parit.ca>

# zodb imports
from persistent.mapping import PersistentMapping

# bokeep imports
from bokeep.prototype_plugin import PrototypePlugin

class SimplePlugin(PrototypePlugin):
    """A simplified front end plugin.  A single instance is created upon first
    use of this plugin.  After that this class is reloaded.
    
    Store the configuration of the associated front end plugin in class
    variables in the class that extends this class."""
    
    # signals to mainwindow.py that this plugin supports the
    # extra keyword argument book when the function
    # returned by get_transaction_edit_interface_hook_from_code is called.
    # To be removed in bokeep 1.1 See mainwindow.py
    SUPPORTS_EXTRA_KEYWORD_ARGUMENTS_ON_VIEW = True
    
    def __init__(self):
        self.trans_registry = PersistentMapping()
        self.type_strings = self.__class__.DEFAULT_TYPE_STRS

    def register_transaction(self, id, transaction):
        """Registers a transaction with this front end plugin, using a unique
        id."""
        
        assert( not self.has_transaction(id) )
        self.trans_registry[id] = transaction

    def remove_transaction(self, id):
        """Removes the transaction with the given id from this front end
        plugin."""
        
        del self.trans_registry[id]

    def has_transaction(self, id):
        """Checks if this front end plugin has a transaction with the given
        id."""
        
        return id in self.trans_registry

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

    @classmethod
    def get_transaction_edit_interface_hook_from_code(cls, code):
        return cls.EDIT_INTERFACES[code]
