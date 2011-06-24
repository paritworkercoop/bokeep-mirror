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
#          Samuel Pauls <samuel@parit.ca>

from persistent import Persistent
import transaction
from BTrees.IOBTree import IOBTree

from backend_plugins.plugin import BackendPlugin

DEFAULT_BACKEND_MODULE = "bokeep.backend_plugins.null"

BOOKS_SUB_DB_KEY = 'books'

class BoKeepDBHandle(object):
    """Generic database management."""
    
    def __init__(self, dbcon):
        self.dbcon = dbcon
        self.dbroot = self.dbcon.root()

    def close(self):
        self.dbcon.close()

    def get_sub_database(self, sub_db):
        return self.dbroot[sub_db]

    def has_sub_database(self, sub_db):
        return sub_db in self.dbroot

    def set_sub_database(self, sub_db, value):
        self.dbroot[sub_db] = value

    def sub_db_changed(self):
        """If you implement your sub database with a class that doesn't
        subclass Persistent, then call this when your sub database changes
        """
        self.dbroot._p_changed = True

    def get_sub_database_do_cls_init(self, sub_db, init_cls,
                                     *args, **kargs):
        if not self.has_sub_database(sub_db):
            self.set_sub_database(sub_db, init_cls(*args, **kargs))
        return self.get_sub_database(sub_db)
        

class BoKeepBookSet(object):
    """High level management of the BoKeep books stored within a database."""
    
    def __init__(self, zodb):
        self.zodb = zodb
        self.dbhandle = self.get_new_dbhandle()
        self.establish_books_sub_db()

    def get_dbhandle(self):
        return self.dbhandle
    
    def get_new_dbhandle(self):
        return BoKeepDBHandle(self.zodb.open())

    # this is slated for deletion
    def get_new_dbcon(self):
        return self.zodb.open()

    def close_primary_connection(self):
        self.dbhandle.close()
   
    def close(self):
        #flush out whatever's pending
        transaction.get().commit()
        for book_name, book in self.iterbooks():
            book.get_backend_plugin().close()
        self.close_primary_connection()
        self.zodb.close()      

    def iterbooks(self):
        return self.dbhandle.get_sub_database(BOOKS_SUB_DB_KEY).iteritems()

    def get_book(self, book_name):
        return self.dbhandle.get_sub_database(BOOKS_SUB_DB_KEY)[book_name]

    def has_book(self, book_name):
        return book_name in self.dbhandle.get_sub_database(BOOKS_SUB_DB_KEY)

    def add_book(self, new_book_name):
        books_dict = self.dbhandle.get_sub_database(BOOKS_SUB_DB_KEY)
        if new_book_name in books_dict:
            raise Exception("a book named %s already exists" % new_book_name )
        books_dict[new_book_name] = book = BoKeepBook(new_book_name)
        self.dbhandle.sub_db_changed()
        return book

    def remove_book(self, book_name):
        books_dict = self.dbhandle.get_sub_database(BOOKS_SUB_DB_KEY)
        del books_dict[book_name]
        self.dbhandle.sub_db_changed()

    def establish_books_sub_db(self):
        self.dbhandle.get_sub_database_do_cls_init(BOOKS_SUB_DB_KEY, dict)

class BoKeepBook(Persistent):
    """A BoKeep book stores the details that are used to create simplified
    balanced accounting transactions.  For example, a BoKeep book may contain
    the hours an employee worked so that it can create an accounting transaction
    on the employee's payday."""
    
    def __init__(self, new_book_name):
        self.book_name = new_book_name
        self.trans_tree = IOBTree()
        self.set_backend_plugin(DEFAULT_BACKEND_MODULE)
        self.enabled_frontend_plugins = {}
        self.disabled_frontend_plugins = {}

    def add_frontend_plugin(self, name):
        """Add a frontend plugin to this BoKeep book, starting in a disabled
        state.  FrontendPluginImportError is thrown if there's a problem."""
        
        assert( name not in self.enabled_frontend_plugins and 
                name not in self.disabled_frontend_plugins )
        # get the module class and instantiate as a new disabled module
        try:
            self.disabled_frontend_plugins[name] =  __import__(
                name, globals(), locals(), [""]).get_plugin_class()()
            self._p_changed = True
        except ImportError:
            raise FrontendPluginImportError(name)

    def enable_frontend_plugin(self, name):
        """Enable a previously added frontend plugin that is currently
        disabled."""
        
        assert( name in self.disabled_frontend_plugins )
        self.enabled_frontend_plugins[name] = self.disabled_frontend_plugins[name]
        del self.disabled_frontend_plugins[name]
        self._p_changed = True
        
    def disable_frontend_plugin(self, name):
        """Disables a presently enabled frontend plugin."""
        
        assert( name in self.enabled_frontend_plugins )
        self.disabled_frontend_plugins[name] = self.enabled_frontend_plugins[name]
        del self.enabled_frontend_plugins[name]
        self._p_changed = True
    
    def get_frontend_plugin(self, name):
        return self.enabled_frontend_plugins[name]

    def get_frontend_plugins(self):
        return self.enabled_frontend_plugins

    def has_enabled_frontend_plugin(self, name):
        return name in self.enabled_frontend_plugins

    def has_disabled_frontend_plugin(self, name):
        return name in self.disabled_frontend_plugins

    def has_frontend_plugin(self, name):
        return self.has_enabled_frontend_plugin(name) or \
               self.has_disabled_frontend_plugin(name)

    def get_iter_of_code_class_module_tripplets(self):
        # there has got to be a more functional way to write this..
        # while also maintaining that good ol iterator don't waste memory
        # property... some kind of nice nested generator expressions
        # with some kind of functional/itertool y thing
        for frontend_plugin in self.enabled_frontend_plugins.itervalues():
            for code in frontend_plugin.get_transaction_type_codes():
                yield (code,
                       frontend_plugin.get_transaction_type_from_code(code),
                       frontend_plugin)

    def get_index_and_code_class_module_tripplet_for_transaction(
        self, trans_id):
        actual_trans = self.get_transaction(trans_id)
        for i, (code, cls, module) in \
                enumerate(self.get_iter_of_code_class_module_tripplets()):
            # the assumption here is that each class only co-responds
            # to one code, that needs to be clarified in the module
            # api
            if module.has_transaction(trans_id) and \
                    actual_trans.__class__ == cls:
                return i, (code, cls, module)
        return None, (None, None, None)

    def set_backend_plugin(self, name):
        if hasattr(self, '_BoKeepBook__backend_module_name'):
            old_backend_module_name = self.get_backend_plugin_name()
            old_backend_module = self.get_backend_plugin()
        try:
            self.__backend_module_name = name
            self.__backend_module = __import__(
              name, globals(), locals(), [""] ).\
    	      get_plugin_class()()
            assert( isinstance(self.__backend_module, BackendPlugin) )
            # because we have changed the backend module, all transactions
            # are now dirty and must be re-written to the new backend module
            for trans_ident, trans in self.trans_tree.iteritems():
                self.__backend_module.mark_transaction_dirty(
                    trans_ident, trans)
            self.__backend_module.flush_backend()
        except ImportError:
            # this is in big trouble if old_backend_module_name isn't set
            # but that should only happen on book instantiation
            self.__backend_module_name = old_backend_module_name
            self.__backend_module = old_backend_module  
            raise BackendPluginImportError(name)

    def get_backend_plugin(self):
        return self.__backend_module

    def get_backend_plugin_name(self):
        return self.__backend_module_name

    backend_plugin = property(get_backend_plugin, set_backend_plugin)

    def insert_transaction(self, trans):
        """Adds a transaction to this BoKeep book."""
        
        if len(self.trans_tree) == 0:
            largest_in_current = -1
        else:
            largest_in_current = self.trans_tree.maxKey()

        if not hasattr(self, 'largest_key_ever'):
            self.largest_key_ever = largest_in_current

        key = max(largest_in_current, self.largest_key_ever) + 1
        self.largest_key_ever = key
        result = self.trans_tree.insert(key, trans)
        assert( result == 1 )
        return key

    def get_transaction_count(self):
        return len(self.trans_tree)

    def has_transaction(self, trans_id):
        return self.trans_tree.has_key(trans_id)

    def get_previous_trans(self, trans_id):
        if not self.has_transaction(trans_id):
            return None
        try:
            prev_key = self.trans_tree.maxKey(trans_id-1)
        except ValueError:
            return None
        else:
            return prev_key
        
    def has_next_trans(self, trans_id):
        return trans_id < self.trans_tree.maxKey()

    def has_previous_trans(self, trans_id):
        return trans_id > self.trans_tree.minKey()

    def get_next_trans(self, trans_id):
        """Returns the key of the next transaction or None."""
        
        if not self.has_transaction(trans_id):
            return None
        try:
            next_key = self.trans_tree.minKey(trans_id+1)
        except ValueError:
            return None
        else:
            return next_key

    def get_transaction(self, trans_id):
        return self.trans_tree[trans_id]

    def get_latest_transaction_id(self):
        if len(self.trans_tree) == 0:
            return None
        else:
            return self.trans_tree.maxKey()

    def remove_transaction(self, trans_id):
        del self.trans_tree[trans_id]
        self.backend_plugin.mark_transaction_for_removal(trans_id)

class FrontendPluginImportError(Exception):
    def __init__(self, plugin_name):
        if type(plugin_name) == str:
            Exception.__init__(self, "%s: missing or broken" % plugin_name)
            self.plugin_names = [plugin_name]
        elif type(plugin_name) == list:
            Exception.__init__(self, "%s: missing or broken" % ', '.join(plugin_name))
            self.plugin_names = plugin_name

class BackendPluginImportError(Exception):
    def __init__(self, plugin_name):
        Exception.__init__(self, "%s: missing or broken" % plugin_name)
