# Copyright (C) 2011-2012 ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
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
from itertools import chain

# zodb imports
from persistent import Persistent
from persistent.mapping import PersistentMapping

# gtk imports
from gtk import \
    VBox, HBox, Window, Button, STOCK_GO_FORWARD, STOCK_GO_BACK, Label, \
    Entry, Calendar, CheckButton, \
    ScrolledWindow, Viewport, POLICY_AUTOMATIC, POLICY_NEVER

# bokeep imports
from bokeep.book_transaction import \
    Transaction, FinancialTransaction, make_fin_line, \
    BoKeepTransactionNotMappableToFinancialTransaction
from bokeep.gtkutil import input_entry_dialog, get_current_date_of_gtkcal, \
    gtk_error_message
from bokeep.gui.gladesupport.glade_util import \
    load_glade_file_get_widgets_and_connect_signals
from bokeep.safe_config_based_plugin_support import \
    SafeConfigBasedPlugin, SafeConfigBasedTransaction, REALLY_BAD_MODULE_NAMES
from bokeep.util import null_function
from bokeep.shells import \
    (TRANSACTION_ALL_EDIT_FIRST_TIME, HEADLESS_MODES )

def get_plugin_class():
    return MultiPageGladePlugin

MULTIPAGEGLADE_CODE = 0

class MultiPageGladePlugin(SafeConfigBasedPlugin, Persistent):
    def __init__(self):
        SafeConfigBasedPlugin.__init__(self) #  self.config_file = None
        self.trans_registry = PersistentMapping()
        self.type_string = "Multi page glade"

    def run_configuration_interface(
        self, parent_window, backend_account_fetch, book):
        config_module_name = input_entry_dialog(
            "Enter a module name", parent=parent_window)
        # check for obvious crap, though we should actually
        # try to import this module as well and look for import error
        if config_module_name in REALLY_BAD_MODULE_NAMES:
            gtk_error_message(
                "%s not a valid module name" % config_module_name)
        else:
            self.set_config_module_name(config_module_name)

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

    @staticmethod
    def get_transaction_display_by_mode_hook(code):
        assert(code == MULTIPAGEGLADE_CODE)
        return multipage_glade_editor

class MultipageGladeTransaction(SafeConfigBasedTransaction):
    def __init__(self, associated_plugin):
        SafeConfigBasedTransaction.__init__(self, associated_plugin)
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

    def config_valid(self, config):
        # delegate to the module level function of the same name
        return config_valid(config)

    def make_new_fin_trans(self):
        # assumption, you've already checked the config and you're really just
        # calling this from __get_and_cache_fin_trans

        config = self.get_configuration_and_provide_on_load_hook()
        try:
            # for debits and credits
            trans_lines = [
                make_fin_line(
                    # just call val_func if debit, else
                    # call it an negate it, note use of
                    # ternary operator
                    val_func(self.widget_states, config) if i==0
                    else -val_func(self.widget_states, config),
                    account, memo)
                for i, deb_or_cred_list in enumerate(config.fin_trans_template)
                for memo, val_func, account in deb_or_cred_list
                ]
            
        except EntryTextToDecimalConversionFail, e:
            raise BoKeepTransactionNotMappableToFinancialTransaction(
                str(e))
        except WidgetFindError, entry_find_e:
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
    return (
        config != None and 
        all(hasattr(config, attr) # all of this attributes must exist
                 for attr in (
                'pages', 'get_currency',
                'gui_initialization_hook',
                'get_description', 'get_chequenum',
                'get_trans_date',
                'page_change_acceptable',
                'page_pre_change_config_hooks',
                'page_post_change_config_hooks',
                'non_decimal_check_labels',
                'blanks_are_fine_for_decimal_coversion_treat_as_zero',
                'fin_trans_template',
                'auto_update_labels' ) # end generator expression
                 )  # end all
                 and
        all(
                  len(page) == 2 and
                  isinstance(page[0], str) and
                  isinstance(page[1], str) 
                  for page in config.pages ) # end all
        ) # end of multiple and expressiont

GLADE_FILE, TOP_WIDGET = range(2)

def make_widget_changed_func(get_state_func):
    def widget_changed(self, widget, *args):
        config = self.plugin.get_configuration(allow_reload=False)
        widget_key = ( (config.pages[self.current_page]),
                       widget.get_name() )
        print 'caught change on', widget_key
        self.trans.update_widget_state(
            widget_key, get_state_func(widget) )
        self.change_register_function()
        self.update_auto_labels()
    return widget_changed

def get_state_of_checkbutton(checkbutton):
    return checkbutton.get_active()

class multipage_glade_editor(object):
    def __init__(self,
                 trans, transid, plugin, gui_parent, change_register_function,
                 book, display_mode=TRANSACTION_ALL_EDIT_FIRST_TIME,
                 transaction_edit_finished_function=null_function):
        self.trans = trans
        self.transid = transid
        self.plugin = plugin
        self.gui_parent = gui_parent
        self.change_register_function = change_register_function
        self.book = book
        self.display_mode = display_mode
        self.transaction_edit_finished_function = (
            null_function if display_mode not in HEADLESS_MODES
            else transaction_edit_finished_function )

        self.hide_parent = Window()
        self.hide_parent.hide()
        self.mainvbox = VBox()
        self.hide_parent.add(self.mainvbox)

        config = self.trans.get_configuration_and_provide_on_load_hook()
        config_module_name = self.plugin.config_module_name
        if not config_valid(config):
            # even in the case of a broken config, we should still
            # display all of the data we have available...
            self.mainvbox.pack_start(Label("no configuration"))
        elif not self.trans.can_safely_proceed_with_config_module(config):
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
                      "the safety of your old information, last adler "
                      "CRC was %s" % self.trans.config_crc_cache ))
        else:
            # if the safety cache was relied on before we need to tell the
            # backend that the transaction is actually dirty,
            # and now that we know that we have a workable config,
            # there's a chance that we'll actually be able to avoid
            # relying on the cache this time
            if self.trans.get_safety_cache_was_used():
                self.change_register_function()

            self.page_label = Label("")
            (x_align, y_align) = self.page_label.get_alignment()
            self.page_label.set_alignment(0.0, y_align)
            self.mainvbox.pack_start(self.page_label, expand=False)

            # establish maincontainer, which is where the actual glade
            # pages are put by attach_current_page
            #
            # The order of placement here is important, we place this
            # after page_label has already been added to main
            # and we also need to do this prior to attach_current_page
            # being called, as it depends on self.maincontainer being
            # there
            #
            # when we're in headless mode the maincontainer can just be
            # the mainvbox itself
            #
            # but, outside headless mode we save screen real-estate and
            # place a scrolled window (which becomes the maincontainer)
            # inside the mainvbox and the glade by glade pages end up
            # in there instead (again, in attach_current_page)
            if display_mode in HEADLESS_MODES:
                self.maincontainer = self.mainvbox
            else:
                self.maincontainer = Viewport()
                sw = ScrolledWindow()
                sw.set_policy(POLICY_NEVER, POLICY_AUTOMATIC)
                sw.add( self.maincontainer)
                self.mainvbox.pack_start(sw)

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
            self.mainvbox.pack_end(button_hbox, expand=False)
            self.nav_buts = dict( (Button(), i)
                                  for i in range(2) )
            for but, i in self.nav_buts.iteritems():
                but.set_property('use-stock', True)
                but.set_label( STOCK_GO_BACK
                               if i == GLADE_BACK_NAV else STOCK_GO_FORWARD )
                button_hbox.pack_start(but, expand=False)
                but.connect("clicked", self.nav_but_clicked)

            config.gui_initialization_hook(
                self, self.trans, self.plugin, self.book)

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
        # go through each page
        for key, widget_dict in self.glade_pages_by_ident_index.iteritems():
            # go through each widget
            for widget_name, widget in widget_dict.iteritems():
                widget_key = (key, widget_name)

                # determine if the current widget is one that we can take
                # care of automatically saving, we do this with a linear
                # search through a table of eligible types,
                # where the first element of each entry is Widget class
                #
                # Once we have a match do one of the following
                #  * Change the widget from the existing stored stage
                #  * Establish new state from some default
                # The next two entries in the table
                # (change_widget_from_state, new_state_from_widget)
                # provide functions to do this
                #
                # Lastly, we establish event handlers for this widget using
                # the last element in the table
                for (cls,
                     change_widget_from_state, new_state_from_widget,
                     establish_event_handlers) in ( # start table

                    (Entry,
                     lambda w, wk: w.set_text(self.trans.get_widget_state(wk)),
                     lambda w: '',
                     lambda w: w.connect("changed", self.entry_changed),
                     ), # Entry

                    (Calendar,
                     self.__change_calendar_from_saved_version,
                     get_current_date_of_gtkcal,
                     lambda w: w.connect( "day_selected",
                                          self.calendar_changed ), 
                     ), # Calendar

                    (CheckButton,
                     lambda w, wk:
                         w.set_active(self.trans.get_widget_state(wk)),
                     get_state_of_checkbutton,
                     lambda w: w.connect("toggled", self.checkbutton_changed),
                     ), # CheckButton

                    ): # end of table and for declartion

                    # does the widget match the type in the current table entry?
                    if isinstance(widget, cls):

                        # use the three remaining functions in the table
                        # as appropriate
                        if self.trans.has_widget_state( widget_key ):
                            change_widget_from_state(widget, widget_key)
                        else:
                            self.trans.update_widget_state(
                                widget_key,
                                new_state_from_widget(widget) )
                        establish_event_handlers(widget)

    def __change_calendar_from_saved_version(self, widget, widget_key):
        date_to_set = self.trans.get_widget_state( widget_key )
        widget.select_month(date_to_set.month-1, date_to_set.year)
        widget.select_day(date_to_set.day)

    def attach_current_page(self):
        config = self.plugin.get_configuration(allow_reload=False)
        self.current_widget_dict = self.glade_pages[self.current_page] 
        self.current_window = self.current_widget_dict[
            config.pages[self.current_page][TOP_WIDGET] ]
        self.current_top_vbox = self.current_window.child
        self.current_top_vbox.reparent(
            self.maincontainer)
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

    def page_change_acceptable_by_input_valid(self):
        bad_fields = ', '.join( widget_name
            for widget_name, widget in self.current_widget_dict.iteritems()
            if not self.widget_valid(widget_name, widget)
            )
        if bad_fields == '':
            return True
        else:
            # this is kind of primiative, it would be better to
            # just highlight them by inserting red lights or something
            gtk_error_message("The following fields are invalid %s" %
                              bad_fields )
            return False
    
    def __current_page_ident(self):
        config = self.plugin.get_configuration(allow_reload=False)
        return config.pages[self.current_page]

    def __entry_widget_is_check_excempt(self, widget_name):
        config = self.plugin.get_configuration(allow_reload=False)
        return (self.__current_page_ident(), widget_name) in \
            config.non_decimal_check_labels

    def widget_valid(self, widget_name, widget):
        config = self.plugin.get_configuration(allow_reload=False)
        if isinstance(widget, Entry) and \
                not self.__entry_widget_is_check_excempt(widget_name):
            try:
                entry_to_decimal_convert(
                    widget.get_text(), widget_name,
                    self.__current_page_ident(),
                    config)
            except EntryTextToDecimalConversionFail:
                return False
        # this covers not only the else case on the first if, but the
        # the case with the above try, except passes without exception
        return True

    def nav_but_clicked(self, but, *args):
        config = self.plugin.get_configuration(allow_reload=False)
        
        old_page = self.current_page
        delta = -1 if self.nav_buts[but] == GLADE_BACK_NAV else 1
        new_page = old_page + delta
        # reject a change outside the acceptable range.. and hmm,
        # perhaps this event handler should never even run under those
        # conditions because we should really just grey the buttons
        if not (new_page < 0 or new_page == len(self.glade_pages)) and \
                self.page_change_acceptable_by_input_valid() and \
                config.page_change_acceptable(self.trans, old_page, new_page):

            # intentionally done before the page is actually attached,
            # that's what we mean by pre
            config.page_pre_change_config_hooks(self.trans, old_page, new_page)

            self.detach_current_page()
            self.current_page = new_page
            self.attach_current_page()
            
            # intentionally done after the page is actually attached,
            # that's what we mean by post
            config.page_post_change_config_hooks(self.trans, old_page, new_page)

    entry_changed = make_widget_changed_func(lambda w: w.get_text() )
    calendar_changed = make_widget_changed_func(get_current_date_of_gtkcal)
    checkbutton_changed = make_widget_changed_func(get_state_of_checkbutton)

    def update_auto_labels(self):
        config = self.plugin.get_configuration(allow_reload=False)
        # this function should never be called if the config hasn't been
        # checked out as okay
        assert( hasattr(config, 'auto_update_labels') )
        for page, label_name, label_source_func in config.auto_update_labels:
            if self.page_is_current(page):
                try:
                    label_text = str(label_source_func(
                            self.trans.widget_states, config))
                except EntryTextToDecimalConversionFail, e:
                    label_text = ''
                except WidgetFindError, no_find_e:
                    label_text = str(no_find_e)
                self.current_widget_dict[label_name].set_text(label_text)

class EntryTextToDecimalConversionFail(Exception):
    pass

class WidgetFindError(Exception):
    pass

def make_sum_entry_val_func(positive_funcs, negative_funcs=()):
    def return_func(*args):
        return sum( chain( (positive_function(*args)
                            for positive_function in positive_funcs),
                           (-negative_function(*args)
                             for negative_function in negative_funcs) ),
                    Decimal(0) )
    return return_func

def entry_to_decimal_convert(txt, entry_name, page_ident, config):
    widget_key = (page_ident, entry_name)
    txt = txt.strip()
    if txt == '' and widget_key in \
                config.blanks_are_fine_for_decimal_coversion_treat_as_zero:
        txt = '0'
    try:
        return Decimal( txt )
    except InvalidOperation:
        raise EntryTextToDecimalConversionFail(
            "entry %s from %s not convertable to decimal with value %s"
            % (entry_name, page_ident,
               txt ) )

def make_get_entry_val_func(page, entry_name):
    def return_func(widget_state_dict, config, *args):
        widget_key = (page, entry_name)
        if widget_key not in widget_state_dict:
            raise WidgetFindError(
                "page and widget %s could not be found" % (page,) )
        return entry_to_decimal_convert(
            widget_state_dict[widget_key], entry_name, page, config)
    return return_func

def make_get_entry_val_func_multi(page, *entry_names):
    return ( make_get_entry_val_func(page, entry_name)
             for entry_name in entry_names )

def make_get_cal_grab_function(page, calendar_name):
    def return_func(widget_state_dict, *args):
        widget_key = (page, calendar_name)
        if widget_key not in widget_state_dict:
            raise WidgetFindError(
                "page and widget %s could not be found" % (page,) )
        return widget_state_dict[widget_key]
    return return_func
