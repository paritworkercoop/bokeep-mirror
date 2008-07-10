#!/usr/bin/env python

# Gtk
import gtk

# Bo-Keep
from bokeep.config import get_database_cfg_file
from bokeep.book import BoKeepBookSet
from bokeep.gui.mainwindow import MainWindow
from bokeep.book_transaction import \
     new_transaction_committing_thread

def bokeep_main():
    bookset = BoKeepBookSet( get_database_cfg_file() )
    commit_thread = new_transaction_committing_thread(bookset)
    window = MainWindow(bookset, commit_thread)
    gtk.main()
    commit_thread.end_trans_thread()
    bookset.close_primary_connection()
    
if __name__ == "__main__":
    bokeep_main()
