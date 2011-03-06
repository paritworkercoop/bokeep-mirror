# Copyright (C) 2011 SkullSpace Winnipeg Inc. <andrew@andreworr.ca>
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
# Author: Mark Jenkins <mark@parit.ca
# Author: Andrew Orr <andrew@andreworr.ca>

def get_plugin_class():
    return MemberFeePlugin

from persistent.list import PersistentList
from persistent.mapping import PersistentMapping
from bokeep.prototype_plugin import PrototypePlugin 
from persistent import Persistent
from bokeep.book_transaction import \
    Transaction, BoKeepTransactionNotMappableToFinancialTransaction, \
    make_common_fin_trans, make_fin_line
from decimal import Decimal
from datetime import date
from itertools import chain # gang

def month_delta(current_date, months=1):
    if not ( 1 <= months <= 12 ):
        raise Exception("months must be between 1 and 12 (for now)")
    new_month = current_date.month + months
    new_year = current_date.year
    if new_month > 12:
        # should really find out how many years and get rid of assert
        # at top
        new_year+=1
        new_month = ((new_month-1) % 12) + 1
    return date(new_year, new_month, current_date.day)

class FeeCollection(Transaction):
    def __init__(self, plugin):
        Transaction.__init__(self, plugin)
        self.collected = Decimal(0)
        self.periods_applied_to = PersistentList()
        self.collection_date = date.today()

    @staticmethod
    def gen_spread_collected(amount, current_date,
                             period_delta, perperiod):
        while amount > 0:
            value_this_period = perperiod
            if value_this_period > amount:
                value_this_period = amount
            yield (current_date, value_this_period)
            current_date  = month_delta(current_date, period_delta)
            amount-=value_this_period
        
    def spread_collected(self, current_date,
                         period_delta, perperiod, amount=None):
        if amount == None:
            amount = self.collected
        self.periods_applied_to = PersistentList(
            FeeCollection.gen_spread_collected(
                amount, current_date, period_delta, perperiod) )

    def get_financial_transactions(self):
        """Return a generator that will provide FinancialTransaction instances
        associated with this bo-keep Transaction to be stored by a
        BackendModule
        """
        if not self.periods_and_collected_match():
            raise BoKeepTransactionNotMappableToFinancialTransaction()

        return chain(
            ( make_common_fin_trans(
                    self.make_collection_lines(), self.collection_date,
                    'collected member fee', currency ), # make_common_fin_trans
              ), # tuple

            self.make_earnings_tranxen()
            ) # chain

    def make_collection_lines(self):
        pass

    def make_earnings_tranxen(self):
        pass

    def sum_of_periods(self):
        return sum( value for date, value in self.periods_applied_to )

    def periods_and_collected_match(self):
        return self.collected == self.sum_of_periods()



class MemberFeePlugin(PrototypePlugin):
    def __init__(self):
        self.transindex = PersistentMapping()

    def register_transaction(self, trans_id, trans):
        """Inform a plugin that a new bokeep transaction, which can be
        edited or viewed by the plugin has become available.

        trans_id - integer identifier for bokeep transaction
        trans - a bokeep.bokeep_transaction.Transaction instance
        """
        self.transindex[trans_id] = trans

    def remove_transaction(self, trans_id):
        """Inform a plugin that a bokeep transaction previously registered
        via register_transaction is no longer available.

        trans_id - integer identifier for bokeep transaction
        """
        del self.transindex[trans_id]

    def has_transaction(self, trans_id):
        """BoKeep asks the plugin if it is taking responsibility for the
        transaction identified by trans_id
        """
        return trans_id in self.transindex

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

