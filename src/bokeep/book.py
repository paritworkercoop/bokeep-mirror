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
from itertools import chain

import ZODB.config
from persistent import Persistent
import transaction
from BTrees.IOBTree import IOBTree

from backend_plugins.plugin import BackendPlugin

DEFAULT_BACKEND_MODULE = "bokeep.backend_plugins.null"

BOOKS_SUB_DB_KEY = 'books'

class BoKeepDBHandle(object):
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
            book.get_backend_module().close()
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
    def __init__(self, new_book_name):
        self.book_name = new_book_name
        self.trans_tree = IOBTree()
        self.set_backend_module(DEFAULT_BACKEND_MODULE)
        self.enabled_modules = {}
        self.disabled_modules = {}

    def add_module(self, module_name):
        assert( module_name not in self.enabled_modules and 
                module_name not in self.disabled_modules )
        # get the module class and instantiate as a new disabled module
        try:
            self.disabled_modules[module_name] =  __import__(
                module_name, globals(), locals(), [""]).get_plugin_class()()
            self._p_changed = True
        except ImportError:
            raise PluginNotFoundError(module_name)

    def enable_module(self, module_name):
        assert( module_name in self.disabled_modules )
        self.enabled_modules[module_name] = self.disabled_modules[module_name]
        del self.disabled_modules[module_name]
        self._p_changed = True
        
    def disable_module(self, module_name):
        assert( module_name in self.enabled_modules )
        self.disabled_modules[module_name] = self.enabled_modules[module_name]
        del self.enabled_modules[module_name]
        self._p_changed = True
    
    def get_module(self, module_name):
        return self.enabled_modules[module_name]

    def get_modules(self):
        return self.enabled_modules

    def has_module_enabled(self, module_name):
        return module_name in self.enabled_modules

    def has_module_disabled(self, module_name):
        return module_name in self.disabled_modules

    def has_module(self, module_name):
        return \
            self.has_module_enabled(module_name) or \
            self.has_module_disabled(module_name)

    def get_iter_of_code_class_module_tripplets(self):
        # there has good to be a more functional way to write this..
        # while also maintaining that good ol iterator don't waste memory
        # property... some kind of nice nested generator expressions
        # with some kind of functional/itertool y thing
        for module in self.enabled_modules.itervalues():
            for code in module.get_transaction_type_codes():
                yield (code, module.get_transaction_type_from_code(code),
                       module)
            
        

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

    def set_backend_module(self, backend_module_name):
        old_backend_module_name = self.get_backend_module_name()
        old_backend_module = self.get_backend_module()
        try:
            self.__backend_module_name = backend_module_name
            self.__backend_module = __import__(
              backend_module_name, globals(), locals(), [""] ).\
    	      get_plugin_class()()
            assert( isinstance(self.__backend_module, BackendPlugin) )
            # because we have changed the backend module, all transactions
            # are now dirty and must be re-written to the new backend module
            for trans_ident, trans in self.trans_tree.iteritems():
                self.__backend_module.mark_transaction_dirty(
                    trans_ident, trans)
            self.__backend_module.flush_backend()
        except ImportError:
            self.__backend_module_name = old_backend_module_name
            self.__backend_module = old_backend_module  
            raise BackendPluginNotFoundError(backend_module_name)

    def get_backend_module(self):
        return self.__backend_module

    def get_backend_module_name(self):
        return self.__backend_module_name

    backend_module = property(get_backend_module, set_backend_module)

    def insert_transaction(self, trans):
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
        self.backend_module.mark_transaction_for_removal(trans_id)

class PluginNotFoundError(Exception):
    def __init__(self, plugin_name):
        if type(plugin_name) == str:
            Exception.__init__(self, "%s: no such plugin." % plugin_name)
            self.plugin_names = [plugin_name]
        elif type(plugin_name) == list:
            Exception.__init__(self, "%s: no such plugin(s)." % ', '.join(plugin_name))
            self.plugin_names = plugin_name

class BackendPluginNotFoundError(Exception):
    def __init__(self, plugin_name):
        Exception.__init__(self, "%s: backend plugin doesn't exist." % plugin_name)
