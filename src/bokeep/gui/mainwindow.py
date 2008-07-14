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

def get_this_module_file_path():
    import mainwindow as mainwindow_module
    return mainwindow_module.__file__

TRANSACTION_AVAILIBLE_SIGNAL = "transaction_availible_signal"

class MainWindow(gobject.GObject):
    __gsignals__ = {
        TRANSACTION_AVAILIBLE_SIGNAL:
            (gobject.SIGNAL_RUN_LAST, None, (str, int))
        }
     
    def __init__(self, bookset, commit_thread):
        gobject.GObject.__init__(self)
        self.bookset = bookset
        self.commit_thread = commit_thread
        self.current_book_name = None
        self.current_transaction_id = None
        self.build_gui()
        
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

    def on_remove(self, window, event):
        main_quit()

    def forward_button_clicked(self, *args):
        pass
    
    def back_button_clicked(self, *args):
        pass

    def new_button_clicked(self, *args):
        pass

    def delete_button_clicked(self, *args):
        pass

    def trans_type_changed(self, *args):
        pass

    def on_books_combobox_changed(self, combobox):
        # close the current book and transaction
        if self.current_book_name != None and \
                self.current_transaction_id != None:
            self.commit_thread.remove_transaction(
                self.current_book_name, self.current_transaction_id )

        # get the new book name
        self.current_book_name = \
            self.books_combobox_model[self.books_combobox.get_active()][1]
        # get the new current book
        book = self.books_combobox_model[self.books_combobox.get_active()][2]

        # the curent transaction becomes the latest in the new book, or
        # None if there is none
        self.current_transaction_id = book.get_latest_transaction_id()

        # First set the trans tpye combo to inactive, which will clear the
        # transaction gui section out
        # if self.current_transaction_id is None, it will stay this way
        # if not None, it will infrom the user that the transaction is
        # loading
        self.trans_type_combo.set_active(-1)
        
        # Second, if there is a non-None current transaction id,
        # tell the commit thread that we would like to be woken
        # up when the current transaction is availible for being
        # acted on. (if there are still changes being made to it, we don't
        # want to read it until they are done)
        #
        # The order matters. If we do this second step first, if we didn't
        # our callback function could be called before the events triggered
        # by self.trans_type_combo.set_active(-1) have been procesed
        if self.current_transaction_id != None:
            self.commit_thread.call_when_entity_uptodate(
                (self.current_book_name, self.current_transaction_id),
                self.emit_transaction_availible_signal )
                
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
