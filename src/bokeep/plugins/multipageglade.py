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
from decimal import Decimal, InvalidOperation
from operator import __and__
from itertools import chain
from os.path import exists

# zodb imports
from persistent import Persistent
from persistent.mapping import PersistentMapping

# gtk imports
from gtk import \
    VBox, HBox, Window, Button, STOCK_GO_FORWARD, STOCK_GO_BACK, Label, \
    Entry, Calendar

# bokeep imports
from bokeep.book_transaction import \
    Transaction, FinancialTransaction, make_fin_line, \
    BoKeepTransactionNotMappableToFinancialTransaction
from bokeep.gtkutil import file_selection_path, get_current_date_of_gtkcal
from bokeep.util import get_module_for_file_path, reload_module_at_filepath, \
    adler32_of_file
from bokeep.gui.gladesupport.glade_util import \
    load_glade_file_get_widgets_and_connect_signals

def get_plugin_class():
    return MultiPageGladePlugin

MULTIPAGEGLADE_CODE = 0

class MultiPageGladePlugin(Persistent):
    def __init__(self):
        self.trans_registry = PersistentMapping()
        self.config_file = None
        self.type_string = "Multi page glade"

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

    def run_configuration_interface(
        self, parent_window, backend_account_fetch):
        old_config_file = self.config_file
        new_config_file = file_selection_path("select config file")
        # should probably make self.config_file a private variable
        # and do this kind of thing in a setter function...
        if old_config_file == new_config_file:
            self.get_configuration() # forces reload if cached
        elif hasattr(self, '_v_configuration'):
            # get rid of cache
            delattr(self, '_v_configuration')
        self.config_file = new_config_file

    def register_transaction(self, front_end_id, trust_trans):
        assert( not self.has_transaction(front_end_id) )
        self.trans_registry[front_end_id] = trust_trans

    def remove_transaction(self, front_end_id):
        del self.trans_registry[front_end_id]

    def has_transaction(self, trans_id):
        return trans_id in self.trans_registry

    @staticmethod
    def get_transaction_type_codes():
        return (MULTIPAGEGLADE_CODE,)

    @staticmethod
    def get_transaction_type_from_code(code):
        assert(code == MULTIPAGEGLADE_CODE)
        return MultipageGladeTransaction

    def get_transaction_type_pulldown_string_from_code(self, code):
        assert(code == MULTIPAGEGLADE_CODE)
        return self.type_string
        
    @staticmethod
    def get_transaction_edit_interface_hook_from_code(code):
        return multipage_glade_editor

class MultipageGladeTransaction(Transaction):
    def __init__(self, associated_plugin):
        Transaction.__init__(self, associated_plugin)
        self.establish_widget_states()

    def establish_widget_states(self):
        if not hasattr(self, 'widget_states'):
            self.widget_states = PersistentMapping()        

    def update_widget_state(self, name, value):
        self.establish_widget_states()
        self.widget_states[name] = value

    def get_widget_state(self, name):
        self.establish_widget_states()
        return self.widget_states[name]

    def has_widget_state(self, name):
        self.establish_widget_states()
        return name in self.widget_states

    def can_safely_proceed_with_config_and_path(self, path, config):
        config_file_path = path
        if not hasattr(self, 'trans_cache'):
            return True
        crc = adler32_of_file(config_file_path)
        return crc == self.config_crc_cache or (
            hasattr(config, 'backwards_config_support') and
            config.backwards_config_support(crc) )

    def get_financial_transactions(self):
        config = self.associated_plugin.get_configuration()
        if hasattr(self, 'trans_cache'):
            config_file_path = self.associated_plugin.config_file
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
        if not config_valid(config):
            raise BoKeepTransactionNotMappableToFinancialTransaction(
                "inadequet config")

        self.trans_cache = self.__make_new_fin_trans()
        
        # important to do this second, as above may exception out, in which
        # case these two cached variables should both not be saved
        self.config_crc_cache = adler32_of_file(
            self.associated_plugin.config_file)

        return self.trans_cache

    def __make_new_fin_trans(self):
        """private for a good reason, read source"""
        # assumption, you've already checked the config and you're really just
        # calling this from __get_and_cache_fin_trans
        config = self.associated_plugin.get_configuration()
        try:
            # for debits and credits
            trans_lines = [
                make_fin_line(
                    # just call val_func if debit, else
                    # call it an negate it, note use of
                    # ternary operator
                    val_func(self.widget_states) if i==0
                    else -val_func(self.widget_states),
                    account, memo)
                for i in range(2)
                for memo, val_func, account in
                config.fin_trans_template[i]
                ]
            
        except EntryTextToDecimalConversionFail, e:
            raise BoKeepTransactionNotMappableToFinancialTransaction(
                str(e))
        except EntryFindError, entry_find_e:
            raise BoKeepTransactionNotMappableToFinancialTransaction(
                str(entry_find_e))
        fin_trans = FinancialTransaction(trans_lines)
        for attr in (
            'trans_date', 'currency', 'chequenum', 'description'):
            setattr(fin_trans, attr,
                    getattr(config, 'get_' + attr)(
                    self.widget_states) )

        return (fin_trans,)

GLADE_BACK_NAV, GLADE_FORWARD_NAV = range(2)

def config_valid(config):
    # has to have the config variable pages, which
    # must consist of a list of two element tuples, each element being a string
    # later on will have to validate that these strings are okay
    #
    # the whole reduce(__and__) thing means we're checking that all elements
    # in the iteration come out True,
    # and each element of that iteration
    # is generated by construction a bool for the validity of each
    # page
    return \
        config != None and \
        reduce( __and__,
                (hasattr(config, attr)
                 for attr in ('pages', 'get_currency',
                             'get_description', 'get_chequenum',
                             'get_trans_date', 'fin_trans_template',
                             'auto_update_labels' )
                 ), # end generator expression
                 True ) and \
        reduce( __and__,
                ( len(page) == 2 and
                  isinstance(page[0], str) and
                  isinstance(page[1], str) 
                  for page in config.pages ),
                True) # end reduce

GLADE_FILE, TOP_WIDGET = range(2)

class multipage_glade_editor(object):
    def __init__(self,
                 trans, transid, plugin, gui_parent, change_register_function):
        self.trans = trans
        self.transid = transid
        self.plugin = plugin
        self.gui_parent = gui_parent
        self.change_register_function = change_register_function

        self.hide_parent = Window()
        self.hide_parent.hide()
        self.mainvbox = VBox()
        self.hide_parent.add(self.mainvbox)

        config = self.plugin.get_configuration()
        config_file_path = self.plugin.config_file
        if not config_valid(config):
            # even in the case of a broken config, we should still
            # display all of the data we have available...
            self.mainvbox.pack_start(Label("no configuration"))
        elif not self.trans.can_safely_proceed_with_config_and_path(
            config_file_path, config):
            # should display all data that's available instead of just
            # this label
            #
            # and should give
            # user an overide option where they either pick an old config
            # for one time use or just blow out the memory of having used
            # a different config...
            #
            # should also print the checksum itself so they know
            # what they need...
            #
            # perhaps eventually we even put in place some archival support
            # for saving old glade and config files and then code into the
            # the transaction -- hey, code you need to be editable is
            # over here..
            #
            # now hopefully there is no marking of this transaction dirty
            # in this mode and the extra safegaurds we put into
            # MultipageGladeTransaction don't get activated
            self.mainvbox.pack_start(
                Label("out of date configuration. data is read only here for "
                      "the safety of your old information"))
        else:
            self.page_label = Label("")
            self.mainvbox.pack_start(self.page_label)

            self.glade_pages = [
                self.__setup_page(glade_file, top_glade_element)
                for glade_file, top_glade_element in config.pages ]
            self.glade_pages_by_ident_index = dict(
                ( (key, self.glade_pages[i])
                  for i, key in enumerate(config.pages)
                  ) # end generator expression
                ) # end dict
            
            self.__setup_auto_widgets()

            self.current_page = 0
            self.attach_current_page()

            button_hbox = HBox()
            self.mainvbox.pack_end(button_hbox)
            self.nav_buts = dict( (Button(), i)
                                  for i in range(2) )
            for but, i in self.nav_buts.iteritems():
                but.set_property('use-stock', True)
                but.set_label( STOCK_GO_BACK
                               if i == GLADE_BACK_NAV else STOCK_GO_FORWARD )
                button_hbox.add(but)
                but.connect("clicked", self.nav_but_clicked)


        self.mainvbox.show_all()
        self.mainvbox.reparent(self.gui_parent)

    def page_is_current(self, page):
        # assumption is that config is fine and we're on a page
        assert( hasattr(self, 'glade_pages_by_ident_index') and
                True )
        return \
            self.glade_pages_by_ident_index[page] == self.current_widget_dict

    def __setup_page(self, glade_file, top_glade_element):
        widget_dict = {}
        
        # this should come from the config, seeing how we're setting up
        # our stuff manually
        event_handlers_dict = {}
        load_glade_file_get_widgets_and_connect_signals(
            glade_file, top_glade_element,
            widget_dict, event_handlers_dict )
        widget_dict[top_glade_element].hide()
        return widget_dict

    def __setup_auto_widgets(self):
        for key, widget_dict in self.glade_pages_by_ident_index.iteritems():
            for widget_name, widget in widget_dict.iteritems():
                widget_key = (key, widget_name)
                for cls, func in (
                    (Entry, self.__setup_auto_entry),
                    (Calendar, self.__setup_auto_calendar), ):
                    if isinstance(widget, cls):
                        func(widget, widget_key)

    def __setup_auto_entry(self, widget, widget_key):
        # important to do the initial set prior to setting up
        # the event handler for changed events
        if self.trans.has_widget_state( widget_key ):
            widget.set_text(
                self.trans.get_widget_state( widget_key ) )
        else:
            self.trans.update_widget_state(widget_key,
                                           '')
        widget.connect( "changed", self.entry_changed )            

    def __setup_auto_calendar(self, widget, widget_key):
        # FIXME, copy-pasted code from __setup_auto_entry, common parts
        # should be commonized... either in __setup_auto_widgets or with
        # a decorator
        # 
        # important to do the initial set prior to setting up
        # the event handler for changed events
        if self.trans.has_widget_state( widget_key ):
            date_to_set = self.trans.get_widget_state( widget_key )
            widget.select_month(date_to_set.month-1, date_to_set.year)
            widget.select_day(date_to_set.day)
        else:
            self.trans.update_widget_state(widget_key,
                                           get_current_date_of_gtkcal(widget) )
        widget.connect( "day_selected", self.calendar_changed )            
        

    def attach_current_page(self):
        config = self.plugin.get_configuration()
        self.current_widget_dict = self.glade_pages[self.current_page] 
        self.current_window = self.current_widget_dict[
            config.pages[self.current_page][TOP_WIDGET] ]
        self.current_top_vbox = self.current_window.child
        self.current_top_vbox.reparent(
            self.mainvbox)
        self.page_label.set_text( "page %s of %s" %( self.current_page + 1,
                                                     len(config.pages) ) )
        self.update_auto_labels()

    def detach_current_page(self):
        # put the spawn back to wence it came
        self.current_top_vbox.reparent(
            self.current_window)

    def detach(self):
        if hasattr(self, 'current_page'):
            self.detach_current_page()
        self.mainvbox.reparent(self.hide_parent)

    def nav_but_clicked(self, but, *args):
        delta = -1 if self.nav_buts[but] == GLADE_BACK_NAV else 1
        new_page = self.current_page + delta
        # reject a change outside the acceptable range.. and hmm,
        # perhaps this event handler should never even run under those
        # conditions because we should really just grey the buttons
        if not (new_page < 0 or new_page == len(self.glade_pages)):
            self.detach_current_page()
            self.current_page = new_page
            self.attach_current_page()

    def entry_changed(self, entry, *args):
        config = self.plugin.get_configuration()
        widget_key = ( (config.pages[self.current_page]), entry.get_name() )
        self.trans.update_widget_state(
            widget_key, entry.get_text() )
        self.change_register_function()
        self.update_auto_labels()

    def calendar_changed(self, calendar, *args):
        # woah, see the commonality with entry_changed, perhaps it's time
        # to do some decorating no?
        print("cal changed")
        config = self.plugin.get_configuration()
        widget_key = ( (config.pages[self.current_page]), calendar.get_name() )
        self.trans.update_widget_state(
            widget_key, get_current_date_of_gtkcal(calendar) )
        self.change_register_function()
        self.update_auto_labels()        
        

    def update_auto_labels(self):
        config = self.plugin.get_configuration()
        # this function should never be called if the config hasn't been
        # checked out as okay
        assert( hasattr(config, 'auto_update_labels') )
        for page, label_name, label_source_func in config.auto_update_labels:
            if self.page_is_current(page):
                try:
                    label_text = str(label_source_func(
                            self.trans.widget_states))
                except EntryTextToDecimalConversionFail, e:
                    label_text = ''
                except EntryFindError, no_find_e:
                    label_text = str(no_find_e)
                self.current_widget_dict[label_name].set_text(label_text)

class EntryTextToDecimalConversionFail(Exception):
    pass

class EntryFindError(Exception):
    pass

def make_sum_entry_val_func(positive_funcs, negative_funcs):
    def return_func(window_list, *args):
        return sum( chain( (positive_function(window_list)
                            for positive_function in positive_funcs),
                           (-negative_function(window_list)
                             for negative_function in negative_funcs) ),
                    Decimal(0) )
    return return_func

def make_get_entry_val_func(page, entry_name):
    def return_func(widget_state_dict, *args):
        widget_key = (page, entry_name)
        if widget_key not in widget_state_dict:
            raise EntryFindError(
                "page and widget %s could not be found" % (page,) )
        try:
            return Decimal( widget_state_dict[widget_key] )
        except InvalidOperation:
            raise EntryTextToDecimalConversionFail(
                "entry %s from %s not convertable to decimal with value %s"
                % (entry_name, widget_key,
                   widget_state_dict[widget_key] ) )
    return return_func
