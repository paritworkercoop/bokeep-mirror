#!/usr/bin/env python
    
# python imports
import sys
from decimal import Decimal

# zopedb imports
import transaction

# bo-keep imports
from bokeep.config import get_database_cfg_file
from bokeep.book import BoKeepBookSet
from bokeep.modules.trust import \
    TrustTransaction, TrustMoneyInTransaction, TrustMoneyOutTransaction
from bokeep.backend_modules.module import BoKeepBackendException

from bokeep.gui.gladesupport.GladeWindow import GladeWindow

from gtk import ListStore, TreeViewColumn, CellRendererText, MessageDialog
import gtk

from datetime import datetime

from bokeep.modules.trust.GUIs.management.trustor_transactions import trustor_transactions

from os.path import abspath, dirname, join, exists

class trustor_management(GladeWindow):
    def __init__(self, bookname):
        self.bookset = BoKeepBookSet( get_database_cfg_file() )
        self.book = self.bookset.get_book(bookname)
        self.backend = self.book.get_backend_module()
        self.trust_module = self.book.get_module('bokeep.modules.trust')
        self.trustors = self.trust_module.get_trustors()
        self.current_name = None

        self.init()

        self.extended_init()

    def construct_filename(self, filename):
        import trustor_management as trust_module
        return join( dirname( abspath( trust_module.__file__ ) ),
                              filename)
    def reset_view(self):
        if self.trustor_view.get_column(0) == None:
            #no columns to remove
            return
        while self.trustor_view.remove_column(self.trustor_view.get_column(0)) > 0:
            pass

    def refresh_trustor_list(self):
        
        self.reset_view()

        self.trustor_list = ListStore( str, str )
        self.trustor_view.set_model(self.trustor_list)


        for i, title in enumerate(('Trustor', 'Balance')):
            self.trustor_view.append_column(
                TreeViewColumn(title,CellRendererText(), text=i ) )

        for trustor in self.trustors:
            self.trustor_list.append([trustor, str(self.trustors[trustor].get_balance())])

    def extended_init(self):
        self.add_widgets('trustor_view', 'dyn_balance')

        
        self.trustor_view = self.widgets['trustor_view']

        self.refresh_trustor_list()

    def init(self):

        filename = 'data/trustor_management.glade'

        widget_list = [
            'TrustManagement',
            'add_button',
            'delete_button',
            'zoom_button',
            'name_entry',
            'save_button',
            'report_button',
            ]

        handlers = [
            'on_window_destroy',
            'on_add_button_clicked',
            'on_delete_button_clicked',
            'on_trustor_view_cursor_changed',
            'on_zoom_button_clicked',
            'on_save_button_clicked',
            'on_report_button_clicked',
            ]

        top_window = 'TrustManagement'
        GladeWindow.__init__(self, self.construct_filename(filename), top_window, widget_list, handlers)

    def on_add_button_clicked(self, *args):
        self.current_name = None
        self.widgets['name_entry'].set_text('')

    def on_delete_button_clicked(self, *args):
        for_delete = self.widgets['name_entry'].get_text()
        self.widgets['name_entry'].set_text('')
        if self.current_name == None:
            return

        trustor = self.trust_module.get_trustor(for_delete)

        if len(trustor.transactions) > 0:
            cantDeleteDia = MessageDialog(flags=gtk.DIALOG_MODAL, message_format='Cannot delete, trustor has associated transacactions.', buttons=gtk.BUTTONS_OK)
            cantDeleteDia.run()
            cantDeleteDia.hide()
        else:            
            self.trust_module.drop_trustor_by_name(for_delete)
            self.refresh_trustor_list()

    def on_zoom_button_clicked(self, *args):
        trustor = self.trust_module.get_trustor(self.current_name)
        trans = trustor_transactions(trustor)
        trans.show()
#        print 'zoom button clicked'

    def on_save_button_clicked(self, *args):
        if self.current_name == None:
            #we're adding someone new
            trustor_name = self.widgets['name_entry'].get_text()
            self.current_name = trustor_name
            self.trust_module.add_trustor_by_name(trustor_name)
            self.refresh_trustor_list()
            trustor_name = self.widgets['name_entry'].set_text('')
        else:
            #we're updating the name of someone who already exists
            new_name = self.widgets['name_entry'].get_text()
            self.trust_module.rename_trustor(self.current_name, new_name)
            self.current_name = new_name            
            self.refresh_trustor_list()

    def set_trustor(self, trustor_selected):
        trustor = self.trust_module.get_trustor(trustor_selected)

        self.current_name = trustor.name
        self.widgets['name_entry'].set_text(trustor.name)
        self.widgets['dyn_balance'].set_text(str(trustor.get_balance()))

    def on_trustor_view_cursor_changed(self, *args):
        sel = self.trustor_view.get_selection()
        sel_iter = sel.get_selected()[1]
        sel_row = self.trustor_list[sel_iter]
        trustor_selected = sel_row[0]
        self.set_trustor(trustor_selected)

    def generate_balance_report(self, filename):
        report_file = open(filename, 'w')
        now = datetime.today()
        nowstring = now.strftime("%B %d, %Y, %H:%M")
        report_file.write("Trustor balance report as at " + nowstring + "\n\n")
        for trustor in self.trustors:
            report_file.write(trustor + ' ' + str(self.trustors[trustor].get_balance()) + '\n')

        report_file.close()

    def on_report_button_clicked(self, *args):
        filesel = gtk.FileSelection(title="Choose report file and location")
        filesel.run()        
        filename = filesel.get_filename()
        filesel.hide()
        self.generate_balance_report(filename)

def main(argv):

    w = trustor_management(argv[1])
    w.show()
    gtk.main()

if __name__ == '__main__':
    main(sys.argv)
