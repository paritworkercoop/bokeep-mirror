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
    """The main BoKeep window.  It contains the BoKeep shell, which in turn
    contains the BoKeep books and their transactions."""
    
    # Functions for window initialization 

    def on_quit_activate(self, args):
        self.application_shutdown()

    def __init__(self, config_path, config, bookset, startup_callback):
        self.gui_built = False
        self.current_editor = None
        self.config_path_and_config_set(config_path, config)
        self.bookset_set(bookset)
        
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

    def config_path_and_config_set(self, config_path, config):
        self.__config_path = config_path
        self.__config = config

    def bookset_set(self, bookset):
        """Sets the set of BoKeep books."""
        
        self.bookset = bookset

    def flush_backend_of_book(self, book):
        """Save the BoKeep book."""
        
        book.get_backend_module().flush_backend()
        transaction.get().commit()

    def close_backend_of_book(self, book):
        """Close the backend used for saving the BoKeep book."""
        
        book.get_backend_module().close()
        transaction.get().commit()

    def application_shutdown(self):
        if hasattr(self, 'guistate'):
            self.guistate.do_action(CLOSE)
        if hasattr(self, 'bookset') and self.bookset != None:
            for bookname, book in self.bookset.iterbooks():
                book.get_backend_module().flush_backend()
                transaction.get().commit()
            self.bookset.close()
            # or, should I be only doing
            # self.bookset.close_primary_connection() instead..?
        main_quit()

    def startup_event_handler(self, *args):
        # this should only be programmed to run once
        assert( hasattr(self, 'startup_event_handler') )
        self.mainwindow.disconnect(self.startup_event_handler)
        # remove the attribute startup_event_handler to intentionally
        # cause the event handler to fail
        delattr(self, 'startup_event_handler')
        assert(not self.gui_built)

        if self.__startup_callback(self.__config_path, self.__config,
                                   self.config_path_and_config_set,
                                   self.bookset_set, self.mainwindow ):
            self.after_background_load()
            assert(self.gui_built)
        else:
            self.application_shutdown()

    def build_gui(self):
        """Setup the BoKeep shell that stores BoKeep transaction GUIs."""
        
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
        """Callback of the book combo box that is used to set the current BoKeep
        book."""
        
        self.guistate.do_action(
            BOOK_CHANGE, 
            self.books_combobox_model[
                self.books_combobox.get_active()][2]
            )

    def refresh_trans_types_and_set_sensitivities_and_status(self):
        """Update the shell's GUI in regard to the types of transactions
        available and also update the sensitivities and status."""
        
        self.refresh_trans_types()
        self.set_sensitivities_and_status()

    def refresh_trans_types(self):
        """Update the shell's GUI in regard to the types of transactions
        available in the current BoKeep book."""
        
        book = self.guistate.get_book()
        if book == None:
            return

        self.programmatic_transcombo_index = True
        self.trans_type_model.clear()
        self.programmatic_transcombo_index = False

        cur_trans = None
        if self.guistate.get_transaction_id() != None:
            cur_trans = book.get_transaction(self.guistate.get_transaction_id())

        modules = book.get_modules()
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

    def set_transcombo_index(self, indx):
        self.programmatic_transcombo_index = True
        self.trans_type_combo.set_active(indx)
        self.programmatic_transcombo_index = False      

    def reset_trans_view(self):
        book = self.guistate.get_book()
        currindex = self.trans_type_combo.get_active_iter()
        currcode = self.trans_type_combo.get_model().get_value(currindex,1)
        currmodule = self.trans_type_combo.get_model().get_value(currindex,2)
        editor_generator = currmodule.\
            get_transaction_edit_interface_hook_from_code(currcode)
        self.clear_trans_view()
        trans_id = self.guistate.get_transaction_id()

        self.current_editor = editor_generator(
                book.get_transaction(trans_id), trans_id, currmodule,
                self.transaction_viewport, self.guistate.record_trans_dirty_in_backend,
                book)

    def clear_trans_view(self):
        """Hide the current transaction so that no transaction is visible in the
        shell."""
        
        if self.current_editor != None: 
            self.current_editor.detach()

    def set_sensitivities_and_status(self):
        """Update the enabled/disabled attributes of the GUI and update the
        status."""
        
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
        total number of transactions."""
        
        if self.gui_built and not(self.guistate.get_book() == None):
            last_trans_id = self.guistate.get_book().get_latest_transaction_id()
            if last_trans_id != None:
                self.transid_label.set_text(
                "%s / %s" %
                (self.guistate.get_transaction_id(), last_trans_id ))
                return # avoid set_text("") below
        self.transid_label.set_text("")

    def set_backend_error_indicator(self):
        """Update the shell's error field."""
        
        # don't bother if the gui isn't built yet
        if not self.gui_built: return

        # set the backend error indicator led
        book = self.guistate.get_book()
        trans_id = self.guistate.get_transaction_id()
        if book != None and trans_id != None:
            backend = book.get_backend_module()
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
        md = MessageDialog(parent = self.mainwindow,
                           type = MESSAGE_ERROR,
                           buttons = BUTTONS_OK,
                           message_format =
                               self.backend_error_msg_label.get_text())
        md.run()
        md.destroy()

    # Functions for use to event handlers, not used during initialization

    def set_trans_type_combo_to_current_and_reset_view(self):
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
        
    def on_new_button_clicked(self, *args):
        """Create a new BoKeep transaction."""
        
        self.guistate.do_action(NEW)
        self.set_trans_type_combo_to_current_and_reset_view()
        self.set_sensitivities_and_status()

    def on_delete_button_clicked(self, *args):
        """Delete a BoKeep transaction."""
        
        self.guistate.do_action(DELETE)
        book = self.guistate.get_book()
        if self.guistate.get_transaction_id() == None:
            self.set_transcombo_index(COMBO_SELECTION_NONE)
            self.clear_trans_view()
        else:
            self.set_trans_type_combo_to_current_and_reset_view()
        self.set_sensitivities_and_status()
        
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
            backend = book.get_backend_module()
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

        currmodule.run_configuration_interface(
            self.mainwindow, self.guistate.get_book().get_backend_module(
                ).backend_account_dialog,
            self.guistate.get_book())
        # hmm, this doesn't seem to be getting it done
        self.clear_trans_view()
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
        self.flush_backend_of_book(self.guistate.get_book())
        self.set_backend_error_indicator()

    def on_backend_close_request(self, *args):
        """Releases the backend that's used to save BoKeep transactions."""
        
        book = self.guistate.get_book()
        if book == None:
            return
        self.flush_backend_of_book(book)
        self.close_backend_of_book(book)
        self.set_backend_error_indicator()
