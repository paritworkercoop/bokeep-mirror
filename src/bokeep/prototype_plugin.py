def get_plugin_class():
    return PrototypePlugin

from persistent import Persistent
from bokeep.book_transaction import Transaction

class PrototypePlugin(Persistent):
    def run_configuration_interface(self, parent_window, backend_account_fetch):
        """Instructs a plugin to run a configuration dialog
        
        parent_window is a gtk.Window which the configuration dialog should
        mark as its parent to do the whole modal dialog thing right
        
        backend_account_fetch is a function that can be called to get an
        account selection dialog from the active backend plugin on the current
        book. It takes a gtk.Window as an argument so there can be adequet modal
        window stacking, and returns of two item tuple, 
        account_spec and account_str .
        - account_spec is an object (of type suited to the backend) that the
        bokeep backend will find to be
        a suitable value for the account_spec attribute of
        bokeep.bokeep_transaction.FinancialTransactionLine
        - account_str is a string that can be used to represent the selected
        account to the user
        """
        pass

    def register_transaction(self, trans_id, trans):
        """Inform a plugin that a new bokeep transaction, which can be
        edited or viewed by the plugin has become available.

        trans_id - integer identifier for bokeep transaction
        trans - a bokeep.bokeep_transaction.Transaction instance
        """
        pass

    def remove_transaction(self, trans_id):
        """Inform a plugin that a bokeep transaction previously registered
        via register_transaction is no longer available.

        trans_id - integer identifier for bokeep transaction
        """
        pass

    def has_transaction(self, trans_id):
        """BoKeep asks the plugin if it is taking responsibility for the
        transaction identified by trans_id
        """
        return False

    @staticmethod
    def get_transaction_type_codes():
        """Return an iterable object (e.g. list, tuple, generator..) of
        integers, where each will stand in as a code for transaction types
        that the plugin supports
        """
        return ()

    @staticmethod
    def get_transaction_type_from_code(code):
        """Takes one of the integer codes from get_transaction_type_codes and
        returns the matching transaction class

        It is essential to implement this function and have it return an
        actuall class if there are codes returned by get_transaction_type_codes
        """
        #return None
        # None is not an allowable return value, but this code should never
        # be reached due to the empty tuple returned from
        # get_transaction_type_codes
        assert(False)
    
    @staticmethod
    def get_transaction_type_pulldown_string_from_code(code):
        """Takes one of the integer codes for transaction types and returns
        a suitable string for representing that transaction type in pull down
        menu in the bo-keep interface
        """
        assert(False)
        return "prototype plugin trans"

    @staticmethod
    def get_transaction_edit_interface_hook_from_code(code):
        """Takes one of the integer codes for transaction types and
        returns a function that can be called at will to create
        an interface for edditing a new transaction.

        The function that is retured should accept the following
        ordered arguments:
          - trans, a bokeep.book_transaction.Transaction instance to be eddited
            by the interface
          - transid, integer identifier for the transaction
          - plugin, the instance of this plugin
          - gui_parent, a gtk.Box that the editing interface should
            call pack_end() on to dynamically insert its interface code
          - change_register_function, to be called by the plugin when it
            wants to tell bokeep that there are changes that it would prefer
            to save. This will result in an eventuall call to
            transaction.get().commit() at sometime in the future when its
            convieneint for bokeep to do so; so plugins should not call
            transaction.get().commit() themselves. After calling this, a plugin
            should be aware that the call to transaction.get().commit()
            could happen at anytime once control is based back to the gui
            thread, so plugins should have themselves in a consistent state
            suitable for database commit when they call this, and
            at any subsequent time at the end of event handlers

            change_register_function also results in bokeep eventually
            calling mark_transaction_dirty in the backend plugin and
            down the line flush_transaction, so the plugins's implentation of
            bokeep.book_transaction.Transaction.get_financial_transactions()
            should be ready to either provide something or raise
            bokeep.book_transaction.
            BoKeepTransactionNotMappableToFinancialTransaction
          
        The function returned here should return an instance of something
        representing the edditing session. This instance must implement
        a detach() method which removes the gtk elements added
        with gui_parent.pack_end()
        """
        def blah(trans, transid, plugin, gui_parent, change_register_function):
            class blah_cls(object):
                def detach(self):
                    pass
            return blah_cls()
        return blah

    def get_transaction_view_interface_hook_from_code(self, code):
        """Takes one of the integer codes for transaction types and
        returns a function for creating an "view" interface.

        The calling convention is the same as it is with
        get_transaction_edit_interface_hook_from_code

        The difference is that BoKeep calls the original function
        when a transaction is created for the first time, and calls
        the one returned here on subsequet views.

        How the plugin treats original edit vs view is entirely up to it
        right now, subsequent views could have no edditing ability, some,
        or all.

        But if you're going for always edit all, you could just skip
        overriding this, as the implementation here just ends up calling
        self.get_transaction_edit_interface_hook_from_code
        """
        
        return self.get_transaction_edit_interface_hook_from_code(code)
