#!/usr/bin/env python

# python imports
from os.path import abspath, dirname, join, exists
from datetime import date
from itertools import chain, islice, izip

# gtk imports
import gtk
from gtk import main_quit
from gtk.glade import XML

# this project imports
from members import member_list, MEMBER_NAME
from glade_util import load_glade_file_get_widgets_and_connect_signals
from transactions import transaction_classes, transaction_view_classes
#from gnucash_thread import GnuCashThread

def main():
    #from sys import argv
    #assert( len(argv) == 2 )
    #gnucash_file = argv[1]
    gnucash_file = ""
    import main as main_module
    glade_file =  join( dirname( abspath( main_module.__file__ ) ),
                        'data', 'parrot_house_money.glade')
    assert( exists( glade_file) )
    main_window = MainWindow( gnucash_file, glade_file )
    
    gtk.main()

class MainWindow(object):
    def __init__(self, gnucash_file, glade_file):
        #self.gnucash_thread = GnuCashThread(gnucash_file)
        self.build_gui(glade_file)

        # TODO, load transactions from file,
        # initialize only if nothing is in file
        self.current_view_type = None
        self.manual_type_set = True
        self.trans_type_combo.set_active(0)
        self.manual_type_set = False
        self.transactions = []
        self.new_button_clicked()

    def build_gui(self, glade_file):
        load_glade_file_get_widgets_and_connect_signals(
            glade_file, "mainwindow", self, self )

        self.view_instances = [ view_class(self, glade_file)
                                for view_class in transaction_view_classes ]
    
    def set_gui_to_current_transaction(self):
        num_transactions = len(self.transactions)

        current_transaction = \
            self.transactions[self.current_transaction_index]
        
        # set back and forward buttons
        self.back_button.set_sensitive(
            self.current_transaction_index != 0 )
        self.forward_button.set_sensitive(
            self.current_transaction_index != (num_transactions-1) )
    
        # set calendar
        self.transaction_date_cal.select_month(
            current_transaction.date.month-1, current_transaction.date.year )
        self.transaction_date_cal.select_day( current_transaction.date.day )

        self.manual_type_set = True
        self.trans_type_combo.set_active(current_transaction.trans_type_index)
        self.manual_type_set = False

        # set the sensitivity of the type choice combo box
        self.trans_type_combo.set_sensitive( not current_transaction.old )

        trans_type = self.trans_type_combo.get_active()
        current_view = self.view_instances[trans_type]
        # set up the transaction type specific view
        if self.current_view_type != trans_type:
            if self.current_view_type != None:
                self.view_instances[self.current_view_type].remove_from_main()

            current_view.send_to_main()
            self.current_view_type = trans_type

        # set values in the transaction type specific view
        current_view.set_transaction( current_transaction )

    def on_remove(self, window, event):
        #self.gnucash_thread.join_init_thread()
        
        for transaction in self.transactions:
            transaction.convert_to_pickable_form()
            #transaction.save_in_gnucash(self.gnucash_thread)
        #self.gnucash_thread.end()
        main_quit()

    def forward_button_clicked(self, *args):
        self.current_transaction_index+=1
        assert( self.current_transaction_index < len(self.transactions) )
        self.set_gui_to_current_transaction()
    
    def back_button_clicked(self, *args):
        self.current_transaction_index-=1
        assert( self.current_transaction_index >= 0 )
        self.set_gui_to_current_transaction()

    def init_current_trans_from_type(self):
        trans_type = self.trans_type_combo.get_active()
        self.transactions[self.current_transaction_index] = \
            transaction_classes[trans_type]()

    def new_button_clicked(self, *args):
        self.transactions.append(None)
        self.current_transaction_index = len(self.transactions)-1
        self.init_current_trans_from_type()
        self.set_gui_to_current_transaction()

    def delete_button_clicked(self, *args):
        pass

    def trans_type_changed(self, *args):
        if not self.manual_type_set:
            self.init_current_trans_from_type()
            self.set_gui_to_current_transaction()


    def cal_day_selected(self, *args):
        current_transaction = \
            self.transactions[self.current_transaction_index]

        (year, month, day) = self.transaction_date_cal.get_date() 
        current_transaction.date = date(year, month+1, day)
        
if __name__ == "__main__":
    main()
