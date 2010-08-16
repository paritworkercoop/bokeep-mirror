# Python library
from os.path import abspath, dirname, join, exists

# ZOPE
import transaction

# Gtk
from gtk import main_quit, ListStore, CellRendererText
from gtk.glade import XML
import gobject



# Bo-Keep
from bokeep.book_transaction import \
     Transaction
from bokeep.gui.glade_util import \
     load_glade_file_get_widgets_and_connect_signals

from bokeep.modules.gui.module import GuiStateMachine

def get_this_module_file_path():
    import mainwindow as mainwindow_module
    return mainwindow_module.__file__

TRANSACTION_AVAILIBLE_SIGNAL = "transaction_availible_signal"
GUI_MODULE = "bokeep.modules.gui"


class MainWindow(gobject.GObject):
    __gsignals__ = {
        TRANSACTION_AVAILIBLE_SIGNAL:
            (gobject.SIGNAL_RUN_LAST, None, (str, int))
        }

    def transaction_count(self):
        book = self.get_current_book()
        return book.get_transaction_count()
     
    def has_transactions(self):
        book = self.get_current_book()
        id = book.get_latest_transaction_id()
        if book.get_latest_transaction_id() == None:
            return False
        else:
            return True

    def set_transcombo_from_type(self, ty):
        i = 0
        for item in self.trans_type_model:
            currtype = item[2].get_transaction_type_from_code(item[1])
            if currtype == ty:
                self.set_transcombo_index(i)
                break
            i += 1


    #go to the requested transaction and set the back/forward button 
    #sensitivity appropriately
    def browse_to_transaction(self, trans_id):
        book = self.get_current_book()
        
        trans = book.get_transaction(trans_id)

        self.sync_to_transaction(trans, trans_id)

    def sync_to_transaction(self, trans, trans_id):
        self.set_transcombo_from_type(type(trans))

        book = self.get_current_book()

        if book.has_previous_trans(trans_id):
            print 'we do indeed have previous for ' + str(trans_id)
            self.set_back_sensitive(True)
        else:
            print 'we do not have previous for ' + str(trans_id)
            self.set_back_sensitive(False)

        if book.has_next_trans(trans_id):
            print 'we do indeed have next for ' + str(trans_id)
            self.set_forward_sensitive(True)
        else:
            print 'we do not have next for ' + str(trans_id)
            self.set_forward_sensitive(False)

        modules = book.get_modules()

        #search for an editor
        editor_creator = None
        edit_module = None
        for module in modules:
            editor_creator = modules[module].get_transaction_edit_interface_hook_from_type(type(trans))
            if not editor_creator == None:
                edit_module = modules[module] 
                break

        self.gui_module.set_trans_location(trans_id)
        self.trans_being_edited = trans
        self.trans_being_edited_id = trans_id

        editor = editor_creator(trans, trans_id, edit_module, self.main_vbox)

        if not self.current_editor == None: 
            self.current_editor.detach()

        self.current_editor = editor

    def load_latest_transaction(self):
        book = self.get_current_book()
    
        latest_id = book.get_latest_transaction_id()
        if latest_id == None:
            return

        trans = book.get_transaction(latest_id)

        self.sync_to_transaction(trans, latest_id)
    
    def set_initial_state(self):
        book = self.get_current_book()

        if not book.has_module(GUI_MODULE):
            print 'can not run without bokeep.modules.gui installed and enabled'
            exit(0)

        self.gui_module = book.get_module(GUI_MODULE)

        initial_state = self.gui_module.get_state()

        if initial_state == None:
            print 'set unknown'
            self.state_machine = GuiStateMachine(GuiStateMachine.UNKNOWN, self, self.gui_module)
            self.state_machine.run_until_steady_state()
        else:
            print 'set ' + str(initial_state)

            self.state_machine = GuiStateMachine(initial_state, self, self.gui_module)
            self.state_machine.run_until_steady_state()

        
    def __init__(self, bookset, commit_thread):
        gobject.GObject.__init__(self)
        self.new_requested = False
        self.new_trans_id = None
        self.gui_built = False
        self.trans_being_edited = None
        self.current_editor = None
        self.bookset = bookset
#        self.commit_thread = commit_thread
        self.current_book_name = None
        self.current_transaction_id = None
        self.build_gui()
        self.gui_built = True
        self.set_initial_state()
        self.programmatic_transcombo_index = False

    def set_transcombo_index(self, indx):        
        self.programmatic_transcombo_index = True
        self.trans_type_combo.set_active(indx)
        self.programmatic_transcombo_index = False

        
    def refresh_trans_types(self):
        book = self.get_current_book()

        self.trans_type_model = ListStore(str, int, object)

        modules = book.get_modules()

        for module in modules:
            trans_codes = modules[module].get_transaction_type_codes()
            for trans_code in trans_codes:
                self.trans_type_model.append([modules[module].get_transaction_type_pulldown_string_from_code(trans_code), trans_code, modules[module]]) 

        self.trans_type_combo.set_model(self.trans_type_model)

    def load_iteration_location(self):
        pass

    def load_state(self):
        pass

    def load_gui_info(self):
        self.load_iteration_location()
        self.load_transaction_mode()

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
        
        for book_name, book in self.bookset.iterbooks():
            self.books_combobox_model.append((book_name, book_name, book))
        if len(self.books_combobox_model) > 0:
            self.books_combobox.set_active(0)

        self.refresh_trans_types()     

    def on_remove(self, window, event):
        #close off the state machine, anything mid-edit can be committed now
        self.new_requested = False        

        self.state_machine.run_until_steady_state()
        main_quit()

    def forward_button_clicked(self, *args):
        self.new_requested = False
        self.state_machine.run_until_steady_state()

        book = self.get_current_book()
 
        next_id, next_trans = book.get_next_trans(self.trans_being_edited_id)

        if next_trans == None:
            #we were mistaken about being able to go next, grey it out
            self.set_forward_sensitive(False)
            return

        self.transaction_being_edited = next_trans
        self.transaction_being_edited_id = next_id
       
        print 'id: ' + str(next_id) + ', trans: ' + str(type(next_trans))
        self.gui_module.set_trans_location(next_id)
        self.sync_to_transaction(next_trans, next_id)

        self.state_machine.run_until_steady_state()
    
    def back_button_clicked(self, *args):
        self.new_requested = False

        self.state_machine.run_until_steady_state()

        book = self.get_current_book()
 
        prior_id, prior_trans = book.get_previous_trans(self.trans_being_edited_id)

        if prior_trans == None:
            #we were mistaken about being able to go back, grey it out
            self.set_back_sensitive(False)
            return

        self.transaction_being_edited = prior_trans
        self.transaction_being_edited_id = prior_id
       
        print 'id: ' + str(prior_id) + ', trans: ' + str(type(prior_trans))
        self.gui_module.set_trans_location(prior_id)

        self.sync_to_transaction(prior_trans, prior_id)

        self.state_machine.run_until_steady_state()

    def new_button_clicked(self, *args):
        self.new_requested = True
        self.new_trans_id = None

        #if we were mid-edit, clicking new commits it so set it back to None
        self.trans_being_edited = None
        self.trans_being_edited_id = None

        self.state_machine.run_until_steady_state()

    def delete_button_clicked(self, *args):
        pass

    def set_back_sensitive(self, sens):
        self.back_button.set_sensitive(sens)

    def set_forward_sensitive(self, sens):
        self.forward_button.set_sensitive(sens)

    def set_delete_sensitive(self, sens):
        self.button6.set_sensitive(sens)
 
    def set_transcombo_sensitive(self, sens):
        self.trans_type_combo.set_sensitive(sens)

    def set_edit_transaction(self, trans):
        book = self.get_current_book()

        if not self.trans_being_edited == None:
            #transaction was in "mid edit" when we changed gears, drop it.
            book.remove_transaction(self.trans_being_edited_id)
            
        self.trans_being_edited = trans
        self.trans_being_edited_id = book.insert_transaction(self.trans_being_edited)

        self.gui_module.set_trans_location(self.trans_being_edited_id)
        self.current_transaction_id = self.trans_being_edited_id

    def reset_trans_view(self):
        currindex = self.trans_type_combo.get_active_iter()
        currcode = self.trans_type_combo.get_model().get_value(currindex,1)
        currmodule = self.trans_type_combo.get_model().get_value(currindex,2)
        editor_generator = currmodule.get_transaction_edit_interface_hook_from_code(currcode)
        self.set_edit_transaction(currmodule.get_transaction_type_from_code(currcode)())
        self.gui_module.set_trans_location(self.trans_being_edited_id)
        if not self.current_editor == None: 
            self.current_editor.detach()
        self.current_editor = editor_generator(self.trans_being_edited, self.trans_being_edited_id, currmodule, self.main_vbox)

    def trans_type_changed(self, *args):
        #only refresh the trans view if it was the user changing the 
        #transaction type
        if not self.programmatic_transcombo_index:
            self.reset_trans_view()

    def get_current_book(self):
        return self.books_combobox_model[self.books_combobox.get_active()][2]

    def get_current_bookname(self):
        return self.books_combobox_model[self.books_combobox.get_active()][1]

    def on_books_combobox_changed(self, combobox):
        #don't mess with stuff until we've finished constructing the gui
        if not self.gui_built:
            return

        book = self.get_current_book()

        # close the current book and transaction
        if self.current_book_name != None and \
                self.current_transaction_id != None:            
            print 'trying a transaction remove'
            book.remove_transaction(self.current_transaction_id)
#            self.commit_thread.remove_transaction(
#                self.current_book_name, self.current_transaction_id )

        # get the new book name
        self.current_book_name = self.get_current_bookname()

        # the curent transaction becomes the latest in the new book, or
        # None if there is none
        self.current_transaction_id = book.get_latest_transaction_id()
        
        self.refresh_trans_types()
        self.set_initial_state()

        # Second, if there is a non-None current transaction id,
        # tell the commit thread that we would like to be woken
        # up when the current transaction is availible for being
        # acted on. (if there are still changes being made to it, we don't
        # want to read it until they are done)
        #
        # The order matters. If we do this second step first, if we didn't
        # our callback function could be called before the events triggered
        # by self.trans_type_combo.set_active(-1) have been procesed
#        if self.current_transaction_id != None:
#            self.commit_thread.call_when_entity_uptodate(
#                (self.current_book_name, self.current_transaction_id),
#                self.emit_transaction_availible_signal )
                
    def emit_transaction_availible_signal(self, book_name, transaction_id):
        # we're going to have to think very carefully about this,
        # what happens when a user requets a load, goes away, and requets
        # it again?
        self.emit(
            TRANSACTION_AVAILIBLE_SIGNAL, book_name, transaction_id)

    def do_transaction_availible_signal(self, book_name, transaction_id):
        if self.current_book_name == book_name and \
                self.current_transaction_id == transaction_id:
            # commit the database so we have the latest
            transaction.get().commit()
            self.bookset.get_book(book_name).get_transaction(transaction_id)
            

gobject.type_register(MainWindow)
