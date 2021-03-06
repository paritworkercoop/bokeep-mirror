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
from bokeep.util import do_module_import, adler32_of_file, null_function
from bokeep.book_transaction import \
    Transaction, BoKeepTransactionNotMappableToFinancialTransaction

REALLY_BAD_MODULE_NAMES = ('', None)

def assert_not_really_bad_module_name(module_name):
    # Samuel, if you're wondering wny the hell I'd risk wasting 
    # resources creating and searching a tuple instead of
    # just doing two comparison ops, well not only is this more
    # "elegant / more DRY" by insane Mark standards, but its also
    # actually caught or will be caught by good python compilers and
    # optimized well to avoid allocating or searching the tuple at all!
    #
    # '' was found to be particularly nasty because passing it to
    # __import__ doesn't result in a import error (it actually imports the
    # bokeep package), but of course such a name isn't found in the
    # sys.modules dictionary when we check there
    assert( module_name not in REALLY_BAD_MODULE_NAMES )

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

    def __configuration_reload(self, call_after_load=null_function):
        assert_not_really_bad_module_name(self.config_module_name)
        assert( hasattr(self, 'config_module_name') )
        assert( hasattr(self, '_v_configuration') )
        assert( self._v_configuration != None )
        assert( self.config_module_name in sys.modules )
        # perhaps we should handle this more gracefully, it's not really
        # something to assert because it could happen outside our control..
        # ..... user could yank file...
        assert( exists(self._v_configuration.__file__) )
        reload(self._v_configuration)
        call_after_load(self._v_configuration)

    def get_configuration(self, allow_reload=False,
                          call_after_load=null_function):
        """Get the configuration module.

        set allow_reload to False if you want to prevent a module reload
        due to file changes
        
        """
        # for backwards compatibility with old versions
        self.__init_config_module_name_if_not_there()

        if hasattr(self, '_v_configuration'):
            if allow_reload:
                self.__configuration_reload(call_after_load)

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
                # immediately do a reload after a successful load,
                # because if a .pyc file or similar is created
                # we're going to end up having that be the value of
                # self._v_configuration.__file__ instead of the original
                # .py file, which is important because we're going to record
                # the checksum of self._v_configuration.__file__ and we
                # want that to be consistent with what we're going to
                # see on the next load
                self.__configuration_reload()
            
            return return_value

    def set_config_module_name(self, new_config_module_name):
        # assert that the caller didn't give us crap
        assert_not_really_bad_module_name(new_config_module_name)

        # for backwards compatibility with old versions
        self.__init_config_module_name_if_not_there()
        
        old_config_module_name = self.config_module_name
        if old_config_module_name == new_config_module_name:
            # even though the module name is unchanged, the module itself
            # may have changed so we reload
            self.__configuration_reload()
        # else its a new config module, and if there's an old cached one
        # we dump the cache
        elif hasattr(self, '_v_configuration'):
            # get rid of cache
            delattr(self, '_v_configuration')
        self.config_module_name = new_config_module_name

SAFTEY_CACHE_USED_STDERR_MSG = """"had to pull transaction from trans cache
due to missing config, but why was a change recorded in the first place?
possible bug elsewhere in code

The only known cause of this so far is editting a config file
while having bo-keep open on a transaction that uses it... the README
for this plugin says don't do that
"""

class SafeConfigBasedTransaction(Transaction):
    """Sublcasses must override config_valid and make_new_fin_trans
    """
    # if __init__ is ever defined make sure it passes appropriate stuff
    # up to Transaction.__init__

    def set_safety_cache_was_used(self):
        """Call when the safety cache is put to use, this sets a flag
        that will cause get_safety_cache_was_used to subsequently return
        True until clear_safety_cache_was_used is called
        """
        self.__safety_cache_was_used = True

    def get_safety_cache_was_used(self):
        """Check if set_safety_cache_was_used was called to flag that
        the safety cache had been put to use (returns True if so)
        This will remain True until clear_safety_cache_was_used
        """
        return getattr(
            self,  '_SafeConfigBasedTransaction__safety_cache_was_used',
            False)

    def clear_safety_cache_was_used(self):
        """Call if the flag safety_cache_was_used is set and no longer should be

        Should only call this if get_safety_cache_was_used() return True
        this condition is asserted.
        
        get_safety_cache_was_used will subsequenlty return False until
        set_safety_cache_was_used is called again.
        """
        assert(self.get_safety_cache_was_used())
        # we re-check what was asserted above in case asserts are disabled
        if self.get_safety_cache_was_used():
            del self.__safety_cache_was_used

    def __config_module_on_load_hook(self, config_module):
        """Pass a reference to this function in some calls to
        SafeConfigBasedPlugin.get_configuration in order to end up
        passing
        """
        getattr(config_module, 'post_module_load_hook', null_function)(
            self, self.associated_plugin, config_module)

    def get_configuration_and_provide_on_load_hook(self):
        # reload is okay here (2nd argument True) as long as 
        # __config_module_on_load_hook is called if a reload
        # occures so that pertinent information can be passed on
        # to the configuration module
        #
        # such information may be important for the module to be able to
        # put the financial transaction together
        return self.associated_plugin.get_configuration(
            True, self.__config_module_on_load_hook)        

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
            hasattr(config_module, 'force_crc_backwards_config') or \
            ( hasattr(config_module, 'backwards_config_support') and
              config_module.backwards_config_support(self.config_crc_cache) )

    def get_financial_transactions(self):
        # its important that if the configuration module is loaded at this
        # point that we call its post-load function to provide it
        # access to info about this transaction and plugin that it may need
        # to generate the financial transaction
        config_module = self.get_configuration_and_provide_on_load_hook()
        if hasattr(self, 'trans_cache'):
            # this whole thing could be avoided if the backend tried to
            # automically first create the new transaction and delete
            # original -- all together, if the first fails we leave in
            # place the original
            if config_module == None:
                print >> sys.stderr, (
                    SAFTEY_CACHE_USED_STDERR_MSG
                    )
                self.set_safety_cache_was_used()
                return self.trans_cache
            if self.can_safely_proceed_with_config_module(config_module):
                return self.__get_and_cache_fin_trans()
            else:
                self.set_safety_cache_was_used()
                print >> sys.stderr, (
                    SAFTEY_CACHE_USED_STDERR_MSG
                    )
                return self.trans_cache
        else:
            return self.__get_and_cache_fin_trans()

    def __get_and_cache_fin_trans(self):
        """private for a good reason, read source"""
        # assumption, you've already checked that there is either no
        # trans in cache or this config is safe to try and your're
        # calling this from get_financial_transactions

        # its important that if the configuration module is loaded at this
        # point that we call its post-load function to provide it
        # access to info about this transaction and plugin that it may need
        # to generate the financial transaction
        config_module = self.get_configuration_and_provide_on_load_hook()
        if not self.config_valid(config_module):
            raise BoKeepTransactionNotMappableToFinancialTransaction(
                "inadequet config")

        self.trans_cache = self.make_new_fin_trans()

        # at this point (above line was fine)
        # we know we managed to create a new backend transaction
        # without relying on the cache, so we clear the safety_cache_was_used
        # flag if in use
        if self.get_safety_cache_was_used():
            self.clear_safety_cache_was_used()

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
