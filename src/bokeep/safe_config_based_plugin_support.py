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

# python imports
from os.path import exists
import sys

# bokeep imports
from bokeep.util import do_module_import, adler32_of_file
from bokeep.book_transaction import \
    Transaction, BoKeepTransactionNotMappableToFinancialTransaction

class SafeConfigBasedPlugin(object):
    def __init__(self):
        self.__init_config_module_name_if_not_there()

    def __init_config_module_name_if_not_there(self):
        """Set self.config_module_name to None if the attribute isn't defined

        used for backwards compatibility reasons because previous versions
        didn't have this attribute
        """
        if not hasattr(self, 'config_module_name'):
            self.config_module_name = None        

    def get_configuration(self, allow_reload=True):
        """Get the configuration module.

        set allow_reload to False if you want to prevent a module reload
        due to file changes
        
        """
        # for backwards compatibility with old versions
        self.__init_config_module_name_if_not_there()

        if hasattr(self, '_v_configuration'):
            assert( self.config_module_name != None )
            assert( self.config_module_name in sys.modules )

            # perhaps we should handle this more gracefully, it's not really
            # something to assert because it could happen outside our control..
            # .....
            assert( exists(self._v_configuration.__file__) )

            if allow_reload:
                current_checksum = adler32_of_file(
                    self._v_configuration.__file__)
                if self._v_configuration_checksum != current_checksum:
                    reload(self._v_configuration)
                    self._v_configuration_checksum = current_checksum

            return self._v_configuration
        else:
            # gee, this isn't safe, should catch exception for import failing
            # or delegate that to do_module_import
            # (BUT BE CAREFUL, do_module_import is used elsewhere where by
            # design the import fail exception is allowed to go up...)
            return_value = \
                None if self.config_module_name == None \
                else do_module_import(self.config_module_name)

            # if we're not returning None, then we should cache what we're
            # returning, but no point setting the cache when it is None
            if return_value != None:
                self._v_configuration = return_value
                self._v_configuration_checksum = adler32_of_file(
                    self._v_configuration.__file__)               
            
            return return_value

    def set_config_module_name(self, new_config_module_name):
        # for backwards compatibility with old versions
        self.__init_config_module_name_if_not_there()
        
        old_config_module_name = self.config_module_name
        if old_config_module_name == new_config_module_name
            # forces reload if old cached module has changed
            self.get_configuration(allow_reload=True)
        # else its a new config module, and if there's an old cached one
        # we dump the cache
        elif hasattr(self, '_v_configuration'):
            # get rid of cache
            delattr(self, '_v_configuration')
            delattr(self, '_v_configuration_checksum')
        self.config_module_name = new_config_module_name

class SafeConfigBasedTransaction(Transaction):
    """Sublcasses must override config_valid and make_new_fin_trans
    """
    # if __init__ is ever defined make sure it passes appropriate stuff
    # up to Transaction.__init__

    def can_safely_proceed_with_config_module(self, config_module):
        """Ensures a configuration module hasn't been tampered with since
        it was last used, or if a new version is permitted

        This is used by get_financial_transactions to avoid replacing
        an original set of backend financial transactions with new ones
        when the old ones were created under separate conditions.

        Returns True if things are fine, False otherwise
        """
        # if doesn't have trans_cache, there there can't be a problem
        # nothing ever done before
        if not hasattr(self, 'trans_cache'):
            return True
        else:
            # would have been created if trans_cache attribute was created
            assert( hasattr(self, 'config_crc_cache') )
        crc = adler32_of_file(config_module.__file__)
        return crc == self.config_crc_cache or \
            hasattr(config, 'force_crc_backwards_config') or \
            ( hasattr(config, 'backwards_config_support') and
              config.backwards_config_support(self.config_crc_cache) )

    def get_financial_transactions(self):
        # by default, a paranoid stance on allow_reload
        config_module = self.associated_plugin.get_configuration(
            allow_reload=False)
        if hasattr(self, 'trans_cache'):
            # this whole thing could be avoided if the backend tried to
            # automically first create the new transaction and delete
            # original -- all together, if the first fails we leave in
            # place the original
            if config_module == None:
                print(
                    "had to pull transaction from trans cache due to missing "
                    "config, but why was a change recorded in the first place?"
                    " possible bug elsewhere in code"
                    )
                return self.trans_cache
            if self.can_safely_proceed_with_config_module(config_module):
                return self.__get_and_cache_fin_trans()
            else:
                print("had to pull transaction from trans cache due to "
                      "incompatible config, but why was a change recorded in "
                      "the first place?"
                      " possible bug elsewhere in code"
                      )
                return self.trans_cache
        else:
            return self.__get_and_cache_fin_trans()

    def __get_and_cache_fin_trans(self):
        """private for a good reason, read source"""
        # assumption, you've already checked that there is either no
        # trans in cache or this config is safe to try and your're
        # calling this from get_financial_transactions
        #
        # paranoid stance on allow_reload
        config_module = self.associated_plugin.get_configuration(
            allow_reload=False)
        if not self.config_valid(config_module):
            raise BoKeepTransactionNotMappableToFinancialTransaction(
                "inadequet config")

        self.trans_cache = self.make_new_fin_trans()
        
        # important to do this second, as above may exception out, in which
        # case these two cached variables should both not be saved
        self.config_crc_cache = adler32_of_file(config_module.__file__)

        return self.trans_cache

    def config_valid(self, config_module):
        raise BoKeepTransactionNotMappableToFinancialTransaction(
            "make_new_fin_trans from SafeConfigBasedTransaction called. "
            "This function shoudl be overridden by a subclass")

    def make_new_fin_trans(self):
        raise BoKeepTransactionNotMappableToFinancialTransaction(
            "make_new_fin_trans from SafeConfigBasedTransaction called. "
            "This function shoudl be overridden by a subclass")
