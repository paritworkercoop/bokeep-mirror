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
from decimal import Decimal
from operator import __and__
from itertools import chain

# zodb imports
from persistent import Persistent
from persistent.mapping import PersistentMapping

# gtk imports
from gtk import \
    VBox, HBox, Window, Button, STOCK_GO_FORWARD, STOCK_GO_BACK, Label, \
    Entry

# bokeep imports
from bokeep.book_transaction import \
    Transaction, FinancialTransaction, make_fin_line, \
    BoKeepTransactionNotMappableToFinancialTransaction
from bokeep.gtkutil import file_selection_path
from bokeep.util import get_module_for_file_path
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
        self.config_file = file_selection_path("select config file")

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

    def get_financial_transactions(self):
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
        hasattr(config, "pages") and \
        reduce( __and__,
                ( len(page) == 2 and
                  isinstance(page[0], str) and
                  isinstance(page[1], str) 
                  for page in config.pages ) )

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
        if not config_valid(config):
            # even in the case of a broken config, we should still
            # display all of the data we have available...
            self.mainvbox.pack_start(Label("no configuration"))
        else:
            self.page_label = Label("")
            self.mainvbox.pack_start(self.page_label)

            self.glade_pages = [
                self.setup_page(glade_file, top_glade_element)
                for glade_file, top_glade_element in config.pages ]
            self.glade_pages_by_ident_index = dict(
                ( (key, self.glade_pages[i])
                  for i, key in enumerate(config.pages)
                  ) # end generator expression
                ) # end dict
            
            for key, widget_dict in self.glade_pages_by_ident_index.iteritems():
                for widget_name, widget in widget_dict.iteritems():
                    widget_key = (key, widget_name)
                    if isinstance(widget, Entry):
                        # important to do the initial set prior to setting up
                        # the event handler for changed events
                        if self.trans.has_widget_state( widget_key ):
                            widget.set_text(
                                self.trans.get_widget_state( widget_key ) )
                        widget.connect( "changed", self.entry_changed )

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

    def setup_page(self, glade_file, top_glade_element):
        widget_dict = {}
        
        # this should come from the config, seeing how we're setting up
        # our stuff manually
        event_handlers_dict = {}
        load_glade_file_get_widgets_and_connect_signals(
            glade_file, top_glade_element,
            widget_dict, event_handlers_dict )
        widget_dict[top_glade_element].hide()
        return widget_dict

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

class EntryTextToDecimalConversionFail(Exception):
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
            raise BoKeepTransactionNotMappableToFinancialTransaction(
                "page and widget %s could not be found" % (page,) )
        try:
            return Decimal( widget_state_dict[widget_key] )
        except ValueError:
            raise EntryTextToDecimalConversionFail(
                "entry %s not convertable to decimal with value "
                "%s" % (entry_name, widget_key,
                        widget_state_dict[widget_key] ) )
    return return_func
