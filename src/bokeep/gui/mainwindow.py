# Copyright (C) 2010  ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
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
# Python library
from os.path import abspath, dirname, join, exists

# ZOPE
import transaction

# Gtk
from gtk import main_quit, ListStore, CellRendererText
from gtk.glade import XML
import gobject


# Bo-Keep
from state import \
    BoKeepGuiState, \
    NEW, DELETE, FORWARD, BACKWARD, TYPE_CHANGE, BOOK_CHANGE, CLOSE
from bokeep.book_transaction import \
     Transaction
from bokeep.gui.gladesupport.glade_util import \
     load_glade_file_get_widgets_and_connect_signals

GUI_STATE_SUB_DB = 'gui_state'

def get_this_module_file_path():
    import mainwindow as mainwindow_module
    return mainwindow_module.__file__

COMBO_SELECTION_NONE = -1

class MainWindow(object):
    # Functions for window initialization 

    def __init__(self, bookset):
        self.gui_built = False
        self.current_editor = None
        self.bookset = bookset
        self.guistate = self.bookset.get_dbhandle().\
            get_sub_database_do_cls_init(
            GUI_STATE_SUB_DB, BoKeepGuiState)
        transaction.get().commit()
        self.build_gui()
        self.gui_built = True
        self.programmatic_transcombo_index = False

    def build_gui(self):
        glade_file = join( dirname( abspath(get_this_module_file_path() ) ),
                           'glade', 'bokeep_main_window.glade' )
        load_glade_file_get_widgets_and_connect_signals(
            glade_file, "mainwindow", self, self )

        self.books_combobox_model = ListStore(str, str, object)
        self.books_combobox.set_model(self.books_combobox_model)
        cell = CellRendererText()
        self.books_combobox.pack_start(cell, True)
        self.books_combobox.add_attribute(cell, 'text', 0)

        cur_book_index = None
        for i, (book_name, book) in enumerate(self.bookset.iterbooks()):
            self.books_combobox_model.append((book_name, book_name, book))
            if self.guistate.get_book() != None and \
                    self.guistate.get_book() == book:
                cur_book_index = i
        if len(self.books_combobox_model) > 0:
            if cur_book_index == None:
                self.books_combobox.set_active(0)
                self.set_book_from_combo()
            else:
                self.books_combobox.set_active(cur_book_index)
        
        self.refresh_trans_types_and_set_sensitivities()

    # Functions for window initialization and use thereafter

    def set_book_from_combo(self):
        self.guistate.do_action(
            BOOK_CHANGE, 
            self.books_combobox_model[
                self.books_combobox.get_active()][2]
            )

    def refresh_trans_types_and_set_sensitivities(self):
        self.refresh_trans_types()
        self.set_sensitivities()

    def refresh_trans_types(self):
        book = self.guistate.get_book()
        if book == None:
            return

        self.trans_type_model = ListStore(str, int, object)

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
            self.main_vbox)

    def clear_trans_view(self):
        if self.current_editor != None: 
            self.current_editor.detach()

    def set_sensitivities(self):
        for (sensitive_widget, action_code) in \
                ( (self.back_button, BACKWARD),
                  (self.forward_button, FORWARD),
                  (self.new_button, NEW),
                  (self.delete_button, DELETE),
                  (self.trans_type_combo, TYPE_CHANGE),
                  (self.books_combobox, BOOK_CHANGE), ):
            sensitive_widget.set_sensitive(
                self.guistate.action_allowed(action_code) )

    # Functions for use to event handlers, not used during initialization

    def set_trans_type_combo_to_current_and_reset_view(self):
        book = self.guistate.get_book()
        trans_id = self.guistate.get_transaction_id()
        assert( trans_id != None )
        assert( isinstance(trans_id, int) )
        self.set_transcombo_index(
            book.get_index_and_code_class_module_tripplet_for_transaction(
                trans_id )[0] )
        self.reset_trans_view()
     
    # Event handlers

    def on_books_combobox_changed(self, combobox):
        #don't mess with stuff until we've finished constructing the gui
        if not self.gui_built:
            return

        self.set_book_from_combo()
        self.refresh_trans_types_and_set_sensitivities()
        
    def new_button_clicked(self, *args):
        self.guistate.do_action(NEW)
        self.set_trans_type_combo_to_current_and_reset_view()
        self.set_sensitivities()

    def delete_button_clicked(self, *args):
        self.guistate.do_action(DELETE)
        book = self.guistate.get_book()
        if self.guistate.get_transaction_id() == None:
            self.set_transcombo_index(COMBO_SELECTION_NONE)
            self.clear_trans_view()
        else:
            self.set_trans_type_combo_to_current_and_reset_view()
        self.set_sensitivities()
        
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
            self.set_sensitivities()

    def forward_button_clicked(self, *args):
        self.guistate.do_action(FORWARD)
        self.set_trans_type_combo_to_current_and_reset_view()
        self.set_sensitivities()
    
    def back_button_clicked(self, *args):
        self.guistate.do_action(BACKWARD)
        self.set_trans_type_combo_to_current_and_reset_view()
        self.set_sensitivities()

    def on_remove(self, window, event):
        self.guistate.do_action(CLOSE)
        main_quit()
    
