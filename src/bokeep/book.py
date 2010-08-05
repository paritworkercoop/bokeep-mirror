import ZODB.config
from persistent import Persistent
import transaction
from BTrees.IOBTree import IOBTree

from backend_modules.module import BackendModule
from util import ends_with_commit

DEFAULT_BACKEND_MODULE = "bokeep.backend_modules.null"

class BoKeepBookSet(object):
    def __init__(self, books_db_conf_file):
        self.zodb = ZODB.config.databaseFromURL(books_db_conf_file)
        self.dbcon = self.get_new_dbcon()
        self.dbroot = self.dbcon.root()

    def get_new_dbcon(self):
        return self.zodb.open()

    def close_primary_connection(self):
        self.dbcon.close()
   
    def close(self):
        #flush out whatever's pending
        transaction.get().commit()
        for book_name, book in self.iterbooks():
            book.get_backend_module().close()
        self.zodb.close()      

    def iterbooks(self):
        return self.dbroot.iteritems()

    def get_book(self, book_name):
        return self.dbroot[book_name]

    def has_book(self, book_name):
        return book_name in self.dbroot

    @ends_with_commit
    def add_book(self, new_book_name):
        assert( new_book_name not in self.dbroot )
        self.dbroot[new_book_name] = book = BoKeepBook(new_book_name)
        return book

    @ends_with_commit
    def remove_book(self, book_name):
        del self.dbroot[book_name]

class BoKeepBook(Persistent):
    def __init__(self, new_book_name):
        self.book_name = new_book_name
        self.trans_tree = IOBTree()
        self.set_backend_module(DEFAULT_BACKEND_MODULE)
        self.enabled_modules = {}
        self.disabled_modules = {}

    @ends_with_commit
    def add_module(self, module_name):
        assert( module_name not in self.enabled_modules and 
                module_name not in self.disabled_modules )
        # get the module class and instantiate as a new disabled module
        self.disabled_modules[module_name] =  __import__(
            module_name, globals(), locals(), [""]).get_module_class()()
        self._p_changed = True

    @ends_with_commit
    def enable_module(self, module_name):
        assert( module_name in self.disabled_modules )
        self.enabled_modules[module_name] = self.disabled_modules[module_name]
        del self.disabled_modules[module_name]
        self._p_changed = True
        
    @ends_with_commit
    def disable_module(self, module_name):
        assert( module_name in self.enabled_modules )
        self.disabled_modules[module_name] = self.enabled_modules[module_name]
        del self.enabled_modules[module_name]
        self._p_changed = True
    
    def get_module(self, module_name):
        return self.enabled_modules[module_name]

    def has_module_enabled(self, module_name):
        return module_name in self.enabled_modules

    def has_module_disabled(self, module_name):
        return module_name in self.disabled_modules

    def has_module(self, module_name):
        return \
            self.has_module_enabled(module_name) or \
            self.has_module_disabled(module_name)

    @ends_with_commit
    def set_backend_module(self, backend_module_name):
        self.__backend_module = __import__(
            backend_module_name, globals(), locals(), [""] ).\
            get_module_class()()
        assert( isinstance(self.__backend_module, BackendModule) )
        # because we have changed the backend module, all transactions
        # are now dirty and must be re-written to the new backend module
        for trans_ident, trans in self.trans_tree.iteritems():
            self.__backend_module.mark_transaction_dirty(
                trans_ident, trans)
        self.__backend_module.flush_backend()

    def get_backend_module(self):
        return self.__backend_module

    backend_module = property(get_backend_module, set_backend_module)

    @ends_with_commit
    def insert_transaction(self, trans):
        if len(self.trans_tree) == 0:
            key = 0
        else:
            key = self.trans_tree.maxKey() + 1
        result = self.trans_tree.insert(key, trans)
        assert( result == 1 )
        return key

    def get_transaction(self, trans_id):
        return self.trans_tree[trans_id]

    def get_latest_transaction_id(self):
        if len(self.trans_tree) == 0:
            return None
        else:
            return self.trans_tree.maxKey()

    @ends_with_commit
    def remove_transaction(self, trans_id):
        del self.trans_tree[trans_id]
        self.backend_module.mark_transaction_for_removal(trans_id)
