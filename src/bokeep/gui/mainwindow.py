# Python library
from os.path import abspath, dirname, join, exists

# Gtk
from gtk import main_quit
from gtk.glade import XML

# Bo-Keep
from bokeep.book_transaction import \
     Transaction
from bokeep.gui.glade_util import \
     load_glade_file_get_widgets_and_connect_signals

def get_this_module_file_path():
    import mainwindow as mainwindow_module
    return mainwindow_module.__file__

class MainWindow(object):
    def __init__(self, bookset, commit_thread):
        self.bookset = bookset
        self.commit_thread = commit_thread
        self.build_gui()
        
    def build_gui(self):
        glade_file = join( dirname( abspath(get_this_module_file_path() ) ),
                           'glade', 'bokeep_main_window.glade' )
        load_glade_file_get_widgets_and_connect_signals(
            glade_file, "mainwindow", self, self )

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
