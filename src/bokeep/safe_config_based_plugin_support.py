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

from bokeep.util import get_module_for_file_path, reload_module_at_filepath, \
    adler32_of_file
from bokeep.book_transaction import \
    BoKeepTransactionNotMappableToFinancialTransaction

class SafeConfigBasedPlugin(object):
    def __init__(self):
        self.config_file = None

    def get_configuration(self):
        if hasattr(self, '_v_configuration'):
            assert( self.config_file != None )
            assert( exists(self.config_file) )
            reload_module_at_filepath(self._v_configuration, self.config_file)
            return self._v_configuration
        else:
            return_value = \
                None if self.config_file == None \
                else get_module_for_file_path(self.config_file)
            if return_value != None:
                self._v_configuration = return_value
            return return_value

    def set_config_file(self, new_config_file):
        old_config_file = self.config_file
        if old_config_file == new_config_file:
            self.get_configuration() # forces reload if cached
        elif hasattr(self, '_v_configuration'):
            # get rid of cache
            delattr(self, '_v_configuration')
        self.config_file = new_config_file

class SafeConfigBasedTransaction(object):
    """Sublcasses must override config_valid and make_new_fin_trans
    """
    def can_safely_proceed_with_config_and_path(self, path, config):
        config_file_path = path
        if not hasattr(self, 'trans_cache'):
            return True
        else:
            # would have been created if trans_cache attribute was
            assert( hasattr(self, 'config_crc_cache') )
        crc = adler32_of_file(config_file_path)
        return crc == self.config_crc_cache or (
            hasattr(config, 'backwards_config_support') and
            config.backwards_config_support(crc) )

    def get_financial_transactions(self):
        config = self.associated_plugin.get_configuration()
        if hasattr(self, 'trans_cache'):
            config_file_path = self.associated_plugin.config_file
            # this whole thing could be avoided if the backend tried to
            # automically first create the new transaction and delete
            # original -- all together, if the first fails we leave in
            # place the original
            if config_file_path == None:
                print(
                    "had to pull transaction from trans cache due to missing "
                    "config, but why was a change recorded in the first place?"
                    " possible bug elsewhere in code"
                    )
                return self.trans_cache
            if self.can_safely_proceed_with_config_and_path(config_file_path,
                                                            config):
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
        config = self.associated_plugin.get_configuration()
        if not self.config_valid(config):
            raise BoKeepTransactionNotMappableToFinancialTransaction(
                "inadequet config")

        self.trans_cache = self.make_new_fin_trans()
        
        # important to do this second, as above may exception out, in which
        # case these two cached variables should both not be saved
        self.config_crc_cache = adler32_of_file(
            self.associated_plugin.config_file)

        return self.trans_cache

    def config_valid(self, config):
        raise BoKeepTransactionNotMappableToFinancialTransaction(
            "make_new_fin_trans from SafeConfigBasedTransaction called. "
            "This function shoudl be overridden by a subclass")

    def make_new_fin_trans(self):
        raise BoKeepTransactionNotMappableToFinancialTransaction(
            "make_new_fin_trans from SafeConfigBasedTransaction called. "
            "This function shoudl be overridden by a subclass")
