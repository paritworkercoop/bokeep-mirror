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
# Authors: Jamie Campbell <jamie@parit.ca>
#          Mark Jenkins <mark@parit.ca>
#          Samuel Pauls <samuel@parit.ca>

import sys

from bokeep.gui.gladesupport.glade_util import \
    do_OldGladeWindowStyleConnect

from gtk import ListStore, TreeViewColumn, CellRendererText
import gtk
from bokeep.plugins.trust import \
    TrustMoneyInTransaction, TrustMoneyOutTransaction

from datetime import datetime

from os.path import abspath, dirname, join, exists

class trustor_transactions(object):
    def __init__(self, trust_module, trustor, trust_manager):
        self.trust_module = trust_module
        self.trustor = trustor
        self.trust_manager = trust_manager

        self.init()
        self.extended_init()
        parent_window = trust_manager.top_window
        self.top_window.set_transient_for(parent_window)
        self.top_window.set_modal(True)

    def construct_filename(self, filename):
        import trustor_management as trust_module
        return join( dirname( abspath( trust_module.__file__ ) ),
                              filename)

    def get_tran_type(self, transaction):
        if isinstance(transaction, TrustMoneyInTransaction):
            return 'In'
        elif isinstance(transaction, TrustMoneyOutTransaction):
            return 'Out'
        else:
            return 'unknown'

    def extended_init(self):
        self.widgets['name_entry'].set_text(self.trustor.name)
        self.widgets['name_entry'].connect('changed', self.on_name_entry_changed)
        
        self.widgets['dyn_balance'].set_text(str(self.trustor.get_balance()))
        
        self.transactions_view = self.widgets['transactions_view']

        self.transactions_list = ListStore( str, str, str )
        self.transactions_view.set_model(self.transactions_list)


        for i, title in enumerate(('Date', 'Type', 'Balance')):
            self.transactions_view.append_column(
                TreeViewColumn(title,CellRendererText(), text=i ) )

        for transaction in self.trustor.transactions:
            self.transactions_list.append([transaction.trans_date.strftime("%B %d, %Y, %H:%M"), self.get_tran_type(transaction), str(transaction.get_transfer_amount())])



    def init(self):

        filename = 'data/trustor_transactions.glade'
        top_window = 'window1'
        do_OldGladeWindowStyleConnect(
            self, self.construct_filename(filename), top_window)

    def generate_transaction_report(self, filename):
        report_file = open(filename, 'w')
        now = datetime.today()
        nowstring = now.strftime("%B %d, %Y, %H:%M")
        report_file.write("Trustor transaction report for " + self.trustor.name + " as at " + nowstring + "\n\n")

        for transaction in self.trustor.transactions:
            report_file.write(transaction.trans_date.strftime("%B %d, %Y, %H:%M") + ' ' + self.get_tran_type(transaction) + ' ' + str(transaction.get_transfer_amount()) + '\n')

        report_file.write('\ncurrent balance: ' + str(self.trustor.get_balance()) + '\n')
        report_file.close()
        
    def on_name_entry_changed(self, *args):
        current_name = self.trustor.name
        new_name = self.widgets['name_entry'].get_text()
        save_button = self.widgets['save_button']
        if current_name != new_name and new_name != '':
            save_button.set_sensitive(True)
        else:
            save_button.set_sensitive(False)

    def on_report_button_clicked(self, *args):
        fcd = gtk.FileChooserDialog(
            "Choose report file and location",
            None,
            gtk.FILE_CHOOSER_ACTION_SAVE,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
             gtk.STOCK_SAVE, gtk.RESPONSE_OK) )
        fcd.set_modal(True)
        result = fcd.run()
        file_path = fcd.get_filename()
        fcd.destroy()
        if result == gtk.RESPONSE_OK and file_path != None:
            self.generate_transaction_report(file_path)
    
    def on_save_button_clicked(self, *args):
        #we're updating the name of someone who already exists
        current_name = self.trustor.name
        new_name = self.widgets['name_entry'].get_text()
        self.trust_module.rename_trustor(current_name, new_name)
        
        # refresh view
        self.trust_manager.refresh_trustor_list()
        self.widgets['save_button'].set_sensitive(False)