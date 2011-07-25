# Copyright (C) 2010-2011  ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
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
# Authors: Mark Jenkins <mark@parit.ca>
#          Samuel Pauls <samuel@parit.ca>

# Python library
from os.path import abspath, dirname, join
import sys

# ZOPE
import transaction

# Gtk
from gtk import main_quit, ListStore, CellRendererText, AboutDialog, \
    MessageDialog, MESSAGE_ERROR, BUTTONS_OK
from gtk.gdk import pixbuf_new_from_file_at_size
import gtk

# Bo-Keep
from state import \
    BoKeepGuiState, \
    NEW, DELETE, FORWARD, BACKWARD, TYPE_CHANGE, BOOK_CHANGE, CLOSE, RESET
from bokeep.gui.gladesupport.glade_util import \
    load_glade_file_get_widgets_and_connect_signals
from bokeep.config import get_bokeep_configuration, \
    BoKeepConfigurationFileException
from bokeep.gui.config.bokeepconfig import establish_bokeep_config
from bokeep.gui.config.bokeepdb import \
    establish_bokeep_db
from main_window_glade import get_main_window_glade_file

GUI_STATE_SUB_DB = 'gui_state'

COMBO_SELECTION_NONE = -1

def shell_startup(config_path, config, bookset, startup_callback):
    """Start the BoKeep GUI that manages BoKeep transactions."""
    
    shell_window = MainWindow(config_path, config, bookset, startup_callback)
    gtk.main()

def shell_startup_config_establish(config_path, e, *cbargs):
    mainwindow = cbargs[0]
    config_path = establish_bokeep_config(mainwindow, (config_path,), e)
    try:
        return ( (None, None)
                 if config_path == None
                 else config_path, get_bokeep_configuration(config_path) )
    except BoKeepConfigurationFileException:
        return None, None

def shell_startup_bookset_fetch(config_path, config, e, *cbargs):
    mainwindow = cbargs[0]
    return establish_bokeep_db(mainwindow, config_path, config, e)

def get_bo_keep_logo():
    """Returns the filename of the BoKeep logo."""
    
    import mainwindow as main_window_module
    return join( dirname( abspath(main_window_module.__file__)),
                 'bo-keep.svg')


class MainWindow(object):
    """Represents the main window for the default BoKeep shell.

    This class has a lot of imperitive/procedural code with plenty of side
    effects, and the cost of them has started to show in subtle bugs.
    It would be a lost worse if the state machine BoKeepGuiState wasn't used.
    Could be a lot better if an even higher level state machine or something
    a lot more functional and a lot less imperitive were used.

    Oh well, in the meantime, here's a depth first major attribute change and
    call tree with some pseudo code
    for the most significant entry points into this class's code.
    Please keep it up to date and also try to reflect in the in per function
    docstrings.
    This is pretty much the only way one can get a big picture overview of
    code like this...

    __init__ (called by shell_startup prior to gtk.main() )
      self.gui_built = False
      self.current_editor = None
      set_config_path_and_config()
      set_bookset()
      build_gui()
        books_combobox and self.books_combobox_model are established
        trans_type_model is established and not connected to the combobox yet
        set_sensitivities_and_status()
          all buttons, combos, and plugin menu are set_sensitive(False) due to
           the gui having not been built yet
          set_backend_error_indicator()
            does nothing due to gui having not been built yet
          set_transid_label()
            label is blanked due to gui having not been built yet
      END build_gui as called by __init__
      self.programmatic_transcombo_index = False
    END __init__

    startup_event_handler (first thing called by gtk.main() )
      if __startup_callback() says go ahead
        after_background_load()
          self.guistate loaded from database (or established if new)
          if no book selected and at least one available
             guistate.do_action(BOOK_CHANGE, first book)
          else if a book selected matches one that exists
             guistate.do_action(RESET)
          else if no book selected that matches, or none even available
             guistate.do_action(BOOK_CHANGE, None)
          books_combobox_model filled in with possible books
          books_combobox set to the current book, or one selected if needed
          if a current book in the combo can not be determined
            books_combobox.set_active(first book)
            set_book_from_combo()
                guistate.do_action(BOOK_CHANGE, current_book_selected)
          else
             books_combobox.set_active( selected book as per self.guistate)
          self.gui_built = True
          refresh_trans_types_and_set_sensitivities_and_status()
            refresh_trans_types()
              exit if no book selected
              trans_type_model is cleared and reconstucted from all active
               plugins, attempt is made to identify transaction type
               matching current transaction (if any)
              trans_type_combo is setup with new model
              if a transaction type was found matching current
                set_transcombo_index()
                reset_trans_view()
                  self.hide_transaction()
                  self.current_editor set with new editor instance  
              else no transaction type found
                hide_transaction()
            END refresh_trans_types as called by..
                 refresh_trans_types_and_set_sensitivities_and_status
            set_sensitivities_and_status()
              all buttons, combos, and plugin menu are set_sensitive
               based on guistate, thanks to gui_built having just become True
              set_backend_error_indicator()
                with gui_built now being true, this updates backend error
                 label and related widgets
              set_transid_label()
                with gui_built now being True, this is set based on current
                 transaction
            END set_sensitivities_and_status() as called by...
                 refresh_trans_types_and_set_sensitivities_and_status
          END refresh_trans_types_and_set_sensitivities_and_status
               as called by after_background_load
        END after_background_load as called by startup_event_handler
      else startup_callback says things can't go on
        self.application_shutdown()
    END startup_event_handler
    
    on_books_combobox_changed (called by gtk gui thread when combo changed)
      exit if not self.gui_built ( this happens during the startup code above)
      set_book_from_combo()
        guistate.do_action(BOOK_CHANGE, newly selected book)
      refresh_trans_types_and_set_sensitivities_and_status()
        refresh_trans_types()
          exit if no book selected (can't happen when combobox triggered)
          trans_type_model is cleared and reconstucted from all active
           plugins, attempt is made to identify transaction type
           matching current transaction (if any)
          trans_type_combo is setup with new model
          if a transaction type was found matching current
            set_transcombo_index()
              reset_trans_view()
                self.hide_transaction()
                self.current_editor set with new editor instance
          else no transaction type found
             hide_transaction()
        END refresh_trans_types as called by..
             refresh_trans_types_and_set_sensitivities_and_status
        set_sensitivities_and_status()
          all buttons, combos, and plugin menu are set_sensitive
           based on guistate, thanks to gui_built having just become True
          set_backend_error_indicator()
            gui_built is definitely true so this updates backend error
             label and related widgets
          set_transid_label()
            gui_built is definitely True, this is set based on current
             transaction
        END set_sensitivities_and_status() as called by...
             refresh_trans_types_and_set_sensitivities_and_statu        
      END refresh_trans_types_and_set_sensitivities_and_status as 
           called by on_books_combobox_changed
    END on_books_combobox_changed
    
    """
    
    # Functions for window initialization 

    def on_quit_activate(self, args):
        self.application_shutdown()

    def __init__(self, config_path, config, bookset, startup_callback):
        self.gui_built = False
        self.current_editor = None
        self.set_config_path_and_config(config_path, config)
        self.set_bookset(bookset)
        
        self.build_gui()
        self.programmatic_transcombo_index = False
        self.__startup_callback = startup_callback

        # program in an event that will only run once on startup
        # the startup_event_handler function will use
        # self.startup_event_handler to disconnect itself
        self.startup_event_handler = self.mainwindow.connect(
            "window-state-event", self.startup_event_handler )
        # should we do an emit to ensure it happens, or be satisfyed
        # that it always happens in tests?

    def set_config_path_and_config(self, config_path, config):
        self.__config_path = config_path
        self.__config = config

    def set_bookset(self, bookset):
        """Sets the set of BoKeep books."""
        
        self.bookset = bookset

    def flush_book_backend(self, book):
        """Save the BoKeep book."""
        
        book.get_backend_plugin().flush_backend()
        transaction.get().commit()

    def close_book_backend(self, book):
        """Close the backend used for saving the BoKeep book."""
        
        book.get_backend_plugin().close()
        transaction.get().commit()

    def application_shutdown(self):
        if hasattr(self, 'guistate'):
            self.guistate.do_action(CLOSE)
        if hasattr(self, 'bookset') and self.bookset != None:
            for bookname, book in self.bookset.iterbooks():
                book.get_backend_plugin().flush_backend()
                transaction.get().commit()
            self.bookset.close()
            # or, should I be only doing
            # self.bookset.close_primary_connection() instead..?
        main_quit()

    def startup_event_handler(self, *args):
        """An event handler programmed to run as soon as gtk's main loop
        takes over

        After disabling itself from running again, this
        calls the __start_callback attribute established in __init__ and
        if that function returns true calls after_background_load for further
        processing. If it fails, application_shutdown() is called

        Part of the motivation here is to defer stuff we didn't want to do
        in __init__ such as calling gtk.main()
        """
        # this should only be programmed to run once
        assert( hasattr(self, 'startup_event_handler') )
        self.mainwindow.disconnect(self.startup_event_handler)
        # remove the attribute startup_event_handler to intentionally
        # cause the event handler to fail
        delattr(self, 'startup_event_handler')
        assert(not self.gui_built)

        # the motivation for making a call back to the high level shell
        # code is that we're able to get the gui thread rolling
        # and have any dialogs that need to be launched by the shell
        # startup code be called at this point, parented to the main
        # window we've managed to build up and get ready in __init__
        if self.__startup_callback(self.__config_path, self.__config,
                                   self.set_config_path_and_config,
                                   self.set_bookset, self.mainwindow ):
            self.after_background_load()
            assert(self.gui_built)
        else:
            self.application_shutdown()

    def build_gui(self):
        """Called by __init__ to take care of the gtk work or putting the
        gui together.

        This consists of loading mainwindow from the glade file,
        setting the bokeep logo, and getting the cell renderers and
        empty models set up for the book and transaction type combo boxes.
        Ends with a a call to set_sensitivities_and_status to nicely
        grey things out until we have something for the shell to actually
        display.

        This is meant to be done without self.book or self.guistate being
        available yet. It shouldn't be called from anywhere other than
        __init__, and only once.
        """
        
        glade_file = get_main_window_glade_file()
        load_glade_file_get_widgets_and_connect_signals(
            glade_file, "mainwindow", self, self )
        self.mainwindow.set_icon_from_file(get_bo_keep_logo())

        self.books_combobox_model = ListStore(str, str, object)
        self.books_combobox.set_model(self.books_combobox_model)
        cell = CellRendererText()
        self.books_combobox.pack_start(cell, True)
        self.books_combobox.add_attribute(cell, 'text', 0)
        self.trans_type_model = ListStore(str, int, object)
        self.set_sensitivities_and_status()
        
    def after_background_load(self):
        """Called to instruct the shell to load from persistent storage the
        last visited book and transaction, sets up the list of books,
        determins the current transaction (if any), sets up the
        transaction type combo for the current bookm and then displays the
        current transaction.

        This is only to be called after the right database is loaded from
        cold, and so far that kind of cold load happens in two places only:
         * at the end of startup_event_handler, which is run once by
           gtk's main thread on shell startup
         * at the end of on_configuration1_activate, where the database
           connection is entirely closed down and possibly even a tottally
           new bookset is loaded
        
        This procedure sets self.guistate right at the start and may call
        self.guistate.do_action with BOOK_CHANGE, and RESET as it determines
        what the current book is. (including possibly None)
        
        Then it builds the list of available books in self.books_combobox_model
        and sets that to whatever the current book is. 

        At that point, the gui can be said to be fully built,
        as all the elements that won't change even when viewing multiple books
        are in place, so self.gui_built = True occures
        The only things left to change are the transaction type combo box
        which can differ per book, and of course the intereface for
        whichever transaction is loaded.

        As a last step, the work described above is done by
        refresh_trans_types_and_set_sensitivities_and_status
        (Be sure to read its docstring)
        """
        self.guistate = (
            self.bookset.get_dbhandle().get_sub_database_do_cls_init(
                GUI_STATE_SUB_DB, BoKeepGuiState) )
        
        # we should do some checking that self.guistate is still reasonable
        # it is possible at this point that the current book or
        # current transaction could be gone due to someone playing with
        # the config or database in some way
        
        bookname_and_book_list = list(self.bookset.iterbooks())
        # if there actually is a book when we think there isn't
        if self.guistate.get_book() == None and len(bookname_and_book_list) > 0:
            self.guistate.do_action(BOOK_CHANGE, bookname_and_book_list[0][1] )
        # if the current book doesn't actually exist anymore
        # this includes the case self.guistate.get_book() == None
        else:
            for book_name, book in bookname_and_book_list:
                # there is a matching book, but it is possible that there
                # is a transaction (when we think none), or the supposedly 
                # current one is gone
                if book == self.guistate.get_book():
                    self.guistate.do_action(RESET)
                    break # else clause below is skipped
            else: # else the current book is no longer in the official list
                self.guistate.do_action(BOOK_CHANGE, None)

        # save the (possibly updated) guistate
        transaction.get().commit()
        
        cur_book_index = None
        for i, (book_name, book) in enumerate(bookname_and_book_list):
            self.books_combobox_model.append((book_name, book_name, book))
            if self.guistate.get_book() != None and \
                    self.guistate.get_book() == book:
                cur_book_index = i
        # this would be the fucked up consequence of a book being deleted
        # ... until we can deal with it, say it can't happen
        assert( not(
                self.guistate.get_book() != None and cur_book_index == None) )
        # should do something similar for the current transaction
        if len(self.books_combobox_model) > 0:
            if cur_book_index == None:
                self.books_combobox.set_active(0)
                self.set_book_from_combo()
            else:
                self.books_combobox.set_active(cur_book_index)
        
        self.gui_built = True

        self.refresh_trans_types_and_set_sensitivities_and_status()

    def closedown_for_config(self):
        """Called soley by on_configuration1_activate to shut down everything
        in the gui prior to running the configuration dialog

        Starts right away by changing self.gui_built = False
        does self.guistate.do_action(CLOSE)
        and clears out the books combo list and transaction type combo list
        """
        self.gui_built = False
        self.guistate.do_action(CLOSE)
        transaction.get().commit() # redundant
        self.books_combobox.set_active(COMBO_SELECTION_NONE)
        self.books_combobox_model.clear()
        self.set_transcombo_index(COMBO_SELECTION_NONE)

        # this clear actually triggers the event handler even after we
        # set to none, I guess losing your model counts as a change!
        self.programmatic_transcombo_index = True
        self.trans_type_model.clear()
        self.programmatic_transcombo_index = False      
        
    # Functions for window initialisation and use thereafter

    def set_book_from_combo(self):
        """Updates self.guistate based on the book selected by the books
        combobox.

        Used by after_background_load and on_books_combobox_changed
        """
        self.guistate.do_action(
            BOOK_CHANGE, 
            self.books_combobox_model[
                self.books_combobox.get_active()][2]
            )

    def refresh_trans_types_and_set_sensitivities_and_status(self):
        """Combines a call to refresh_trans_types and
        set_sensitivities_and_status. in that order
        
        See the respective docstrings

        used by
         * after_background_load as a last step after figuring out the current
           book, constructing the book list, and setting the current book
         * on_books_combobox_changed as a last step after a new book is
           selected
        """
        self.refresh_trans_types()
        self.set_sensitivities_and_status()

    def refresh_trans_types(self):
        """Updates the transaction type combobox to reflect the currently
        selected book and transaction -- then calls self.reset_trans_view()
        to display the current transaction or hide_transaction() to at
        least clear off the old one.

        Does nothing if there isn't a currently selected book
        Alters the state of self.trans_type_model
        Calls reset_trans_view if a transaction type is selected.
        One of the things it does is call hide_transaction()
        Directly call hide_transaction() if there is no transaction type
        selected, in either case we want to be sure there isn't an old gui
        hanging around.
        """
        
        book = self.guistate.get_book()
        if book == None:
            return

        self.programmatic_transcombo_index = True
        self.trans_type_model.clear()
        self.programmatic_transcombo_index = False

        cur_trans = None
        if self.guistate.get_transaction_id() != None:
            cur_trans = book.get_transaction(self.guistate.get_transaction_id())

        frontend_plugins = book.get_frontend_plugins()
        current_trans_type_index = COMBO_SELECTION_NONE
        for i, (code, trans_cls, module) in \
                enumerate(book.get_iter_of_code_class_module_tripplets()):
            self.trans_type_model.append( (
                module.get_transaction_type_pulldown_string_from_code(code),
                code, module ) )
            if cur_trans != None and isinstance(cur_trans, trans_cls):
                current_trans_type_index = i

        self.trans_type_combo.set_model(self.trans_type_model)
        assert( self.trans_type_combo.get_active() == COMBO_SELECTION_NONE )

        if current_trans_type_index != COMBO_SELECTION_NONE:
            self.set_transcombo_index(current_trans_type_index)
            self.reset_trans_view()
        else:
            self.hide_transaction()

    def set_transcombo_index(self, indx):
        """Changed the currently selected transaction type combobox to the
        specified type by index in that combobox

        The event handler, trans_type_changed is prevented from running
        """
        self.programmatic_transcombo_index = True
        self.trans_type_combo.set_active(indx)
        self.programmatic_transcombo_index = False      

    def reset_trans_view(self):
        """Clears away an old transaction editor (if present) with
        hide_transaction and starts up a new one for the current transaction

        It's assumed here that self.guistate does specify a book, transaction,
        and current transaction type to provide an editor. So don't
        call this when that isn't true.

        Called, in this assumed context by, refresh_trans_types,
        set_trans_type_combo_to_current_and_reset_view, trans_type_changed,
        on_configure_plugin1_activate
        """
        book = self.guistate.get_book()
        currindex = self.trans_type_combo.get_active_iter()
        currcode = self.trans_type_combo.get_model().get_value(currindex,1)
        currmodule = self.trans_type_combo.get_model().get_value(currindex,2)
        editor_generator = currmodule.\
            get_transaction_edit_interface_hook_from_code(currcode)
        self.hide_transaction()
        trans_id = self.guistate.get_transaction_id()

        self.current_editor = editor_generator(
                book.get_transaction(trans_id), trans_id, currmodule,
                self.transaction_viewport, self.guistate.record_trans_dirty_in_backend,
                book)

    def hide_transaction(self):
        """If a transaction is currently displayed (self.current_editor),
        detach it.
        """
        
        if self.current_editor != None: 
            self.current_editor.detach()

    def set_sensitivities_and_status(self):
        """Update the enabled/disabled attributes of the GUI and update the
        status.

        Specifically, this uses checks for action permissability from
        self.guistate to set the sensitivity of the toolbar buttons,
        the books and transaction type comboxes, and the plugin menu.
        These checks are done conditional on self.gui_built being set
        otherwise they're always set to disabled.

        After those we call set_backend_error_indicator and
        self.set_transid_label, see thier docstrings
        """
        
        for (sensitive_widget, action_code) in \
                ( (self.back_button, BACKWARD),
                  (self.forward_button, FORWARD),
                  (self.new_button, NEW),
                  (self.delete_button, DELETE),
                  (self.trans_type_combo, TYPE_CHANGE),
                  (self.books_combobox, BOOK_CHANGE),
                  (self.plugin1, DELETE),
                  (self.plugin1_menu, DELETE), ):
                if self.gui_built:
                    sensitive_widget.set_sensitive(
                        self.guistate.action_allowed(action_code) )
                else:
                    sensitive_widget.set_sensitive(False)

        self.set_backend_error_indicator()
        self.set_transid_label()

    def set_transid_label(self):
        """Update the field indicating the current transaction index out of the
        total number of transactions.

        Only does this if self.gui_built is set ans there's a book selected,
        otherwise just sets the label blank

        Only called from set_transid_label
        """
        
        if self.gui_built and not(self.guistate.get_book() == None):
            last_trans_id = self.guistate.get_book().get_latest_transaction_id()
            if last_trans_id != None:
                self.transid_label.set_text(
                "%s / %s" %
                (self.guistate.get_transaction_id(), last_trans_id ))
                return # avoid set_text("") below
        self.transid_label.set_text("")

    def set_backend_error_indicator(self):
        """Updates the label and related widgets for displaying backend
        plugin errors with info from the active book's backend plugin

        Doesn't do anything if self.gui_built is not set, also does
        nothing if there isn't a book and transaction selected.

        Called by set_sensitivities_and_status, on_backend_flush_request,
        and on_backend_close_request
        """
        
        # don't bother if the gui isn't built yet
        if not self.gui_built: return

        # set the backend error indicator led
        book = self.guistate.get_book()
        trans_id = self.guistate.get_transaction_id()
        if book != None and trans_id != None:
            backend = book.get_backend_plugin()
            if backend.transaction_is_clean(trans_id):
                self.backend_error_light.hide()
                self.backend_error_msg_label.hide()
                self.error_details_button.hide()
            else:
                self.backend_error_light.show()
                self.backend_error_msg_label.set_text(
                    backend.reason_transaction_is_dirty(trans_id) )
                self.backend_error_msg_label.show()
                self.error_details_button.show()

    def on_error_details_button_clicked(self, *args):
        """Event handler for the user requesting to see the full backend
        plugin error display
        """
        md = MessageDialog(parent = self.mainwindow,
                           type = MESSAGE_ERROR,
                           buttons = BUTTONS_OK,
                           message_format =
                               self.backend_error_msg_label.get_text())
        md.run()
        md.destroy()

    # Functions for use to event handlers, not used during initialization

    def set_trans_type_combo_to_current_and_reset_view(self):
        """Call after the current transaction has changed from one to
        another within the same book to update the transaction type combo
        box and to update the editor interface.

        Another key note is that this doesn't change what's listed in the
        list of transaction types like refresh_trans_types does, just
        ensures the right one is used and applies the editor interface for it.

        This is called only by the only places it makes sense right now:
        new_button_clicked, delete_button_clicked (only if a transaction
        remains), on_forward_button_clicked, on_back_button_clicked .
        Notice how all of the above involve situations where prior to them
        a book was already being viewed and the transaction type list was
        already in place, and the only thing that happened was a switch
        to different transaction and a need to just display it.

        This calls reset_trans_view as a last step to take care of
        removing the old transaction from the display and displaying the
        new one
        """
        book = self.guistate.get_book()
        trans_id = self.guistate.get_transaction_id()
        assert( trans_id != None )
        assert( isinstance(trans_id, int) )
        (i, (a, b, c)) = \
            book.get_index_and_code_class_module_tripplet_for_transaction(                trans_id )
        # What the hell, why is i None sometimes,
        # (trans id not found in any module) --
        # this is a bug that has come up
        #assert( i != None)
        # should really have kept that assertion in.. but due to bugs I
        # have cheated..
        if i == None:
            i = COMBO_SELECTION_NONE
            # if this is actually still happening, perhaps we
            # want a hide_transaction() here so we at least clear
            # off the old gui (if still there...)
        self.set_transcombo_index(i)
        if i != COMBO_SELECTION_NONE:
            self.reset_trans_view()
     
    # Event handlers

    def on_books_combobox_changed(self, combobox):
        """Change the current BoKeep book."""
        
        #don't mess with stuff until we've finished constructing the gui
        if not self.gui_built:
            return

        self.set_book_from_combo()
        self.refresh_trans_types_and_set_sensitivities_and_status()
        
    def new_button_clicked(self, *args):
        """Create a new BoKeep transaction."""
        self.guistate.do_action(NEW)
        self.set_trans_type_combo_to_current_and_reset_view()
        self.set_sensitivities_and_status()

    # to maintain compatibility with listing of event handler in
    # the glade file.
    # we don't change the glade file because those are impossible to
    # maintain and merge in when developing in a branch, so once
    # this code is merged to default the glade file can be updated
    # and this comment and backwards compatibility assignment can be
    # removed
    on_new_button_clicked = new_button_clicked

    def delete_button_clicked(self, *args):
        """Delete a BoKeep transaction."""
        
        self.guistate.do_action(DELETE)
        book = self.guistate.get_book()
        if self.guistate.get_transaction_id() == None:
            self.set_transcombo_index(COMBO_SELECTION_NONE)
            self.hide_transaction()
        else:
            self.set_trans_type_combo_to_current_and_reset_view()
        self.set_sensitivities_and_status()

    # see comment on on_new_button_clicked
    on_delete_button_clicked = delete_button_clicked

    def trans_type_changed(self, *args):
        """Event handler for when the transaction type on a new transaction
        changes
        """
        #only refresh the trans view if it was the user changing the 
        #transaction type
        if not self.programmatic_transcombo_index:
            assert( self.gui_built ) # and never during gui building..

            # odd, when this was called without the second argument, the
            # program rightly crashed if a NEW transaction was created,
            # followed by TYPE_CHANGE here. But, on re-launch, the memory of
            # the old type transaction seemed to remain in the state
            # stuff but was no longer available in the book. The
            # zodb transaction should of prevented this, what gives?
            self.guistate.do_action(TYPE_CHANGE,
                                    self.trans_type_combo.get_active())
            self.reset_trans_view()
            self.set_sensitivities_and_status()

    def on_forward_button_clicked(self, *args):
        """Go forward to next transaction."""
        
        self.guistate.do_action(FORWARD)
        self.set_trans_type_combo_to_current_and_reset_view()
        self.set_sensitivities_and_status()
    
    def on_back_button_clicked(self, *args):
        """Go back to previous transaction."""
        
        self.guistate.do_action(BACKWARD)
        self.set_trans_type_combo_to_current_and_reset_view()
        self.set_sensitivities_and_status()

    def on_remove(self, window, event):
        self.application_shutdown()
    
    def on_configuration1_activate(self, *args):
        """Configure BoKeep."""
        
        assert( self.gui_built )
        self.closedown_for_config()
        self.bookset.close()
        assert( not self.gui_built )

        # major flaw right now is that we don't want this to
        # re-open the same DB at the end, and we need to do something
        # the return value and seting bookset
        self.bookset = \
            establish_bokeep_db(self.mainwindow, self.__config_path, self.__config, None)

        # if there's uncommited stuff, we need to ditch it because
        # the above function killed off and re-opened the db connecion
        # we had. But, if there aren't any changes anywhere, this shuldn't
        # be a problem, right? .. but on the other hand a new transaction
        # probably begins as new one dies
        transaction.get().abort()

        if self.bookset == None:
            sys.exit()

        self.after_background_load()
        assert( self.gui_built )
        

    def on_configure_backend1_activate(self, *args):
        """Configure the backend plugin."""
        
        book = self.guistate.get_book()
        if book != None:
            backend = book.get_backend_plugin()
            backend.close()
            backend.configure_backend(self.mainwindow)
            transaction.get().commit()

    def on_configure_plugin1_activate(self, *args):
        """Configure the current front end plugin."""
        
        # the gui should never allow this event handler to be triggered
        # if there is no transaction and thus no associated plugin
        # to configure
        assert( self.guistate.get_book() != None )
        assert( self.guistate.get_transaction_id() != None )

        currindex = self.trans_type_combo.get_active_iter()
        if currindex == COMBO_SELECTION_NONE:
            return
        currmodule = self.trans_type_combo.get_model().get_value(
            currindex,2)

        # technically not needed, as the self.reset_trans_view below
        # does this as well
        #
        # For now, nice to leave this in hear because it makes solutions
        # to bug #32815 much easier to test, you can see right away
        # once the config dialog below comes up if the detatch operation
        # was a success
        self.hide_transaction()

        currmodule.run_configuration_interface(
            self.mainwindow, self.guistate.get_book().get_backend_plugin(
                ).backend_account_dialog,
            self.guistate.get_book())
        self.reset_trans_view()
        transaction.get().commit()

    def on_about_activate(self, *args):
        """Displays the Help > About dialog."""
        
        bo_keep_logo_path = get_bo_keep_logo()
        ab = AboutDialog()
        ab.set_transient_for(self.mainwindow)
        ab.set_modal(True)
        ab.set_name("Bo-Keep")
        ab.set_version("1.1.1")
        ab.set_copyright("ParIT Worker Co-operative, Ltd. 2006-2011")
        ab.set_comments(
            """Bo-Keep helps you keep your books so you don't get lost.

Developed with grant funding from:
 - Assiniboine Credit Union <http://assiniboine.mb.ca>
 - Legal Aid Manitoba <http://www.legalaid.mb.ca>
""")
        ab.set_license(
"""Bo-Keep is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
""")
        ab.set_authors(("Mark Jenkins <mark@parit.ca>",
                        "Jamie Campbell <jamie@parit.ca>",
                        "Samuel Pauls <samuel@parit.ca>",
                        "Andrew Orr <andrew@andreworr.ca>",
                        "Sara Arenson <sara_arenson@yahoo.ca>",))
        ab.set_artists(("David Henry <work@davidhenry.ca>",))
        ab.set_program_name("Bo-Keep")
        ab.set_logo( pixbuf_new_from_file_at_size(
                bo_keep_logo_path, 300, 266) )
        ab.run()
        ab.destroy()

    def on_backend_flush_request(self, *args):
        """Saves the BoKeep transactions."""
        
        if self.guistate.get_book() == None:
            return
        self.flush_book_backend(self.guistate.get_book())
        self.set_backend_error_indicator()

    def on_backend_close_request(self, *args):
        """Releases the backend that's used to save BoKeep transactions."""
        
        book = self.guistate.get_book()
        if book == None:
            return
        self.flush_book_backend(book)
        self.close_book_backend(book)
        self.set_backend_error_indicator()
