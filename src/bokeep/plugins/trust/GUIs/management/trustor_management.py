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

# python imports
from decimal import Decimal

# zopedb imports
import transaction

# bo-keep imports
from bokeep.plugins.trust import \
    TrustTransaction, TrustMoneyInTransaction, TrustMoneyOutTransaction

from bokeep.gui.gladesupport.glade_util import \
    do_OldGladeWindowStyleConnect

from gtk import ListStore, TreeViewColumn, CellRendererText, MessageDialog, \
    MESSAGE_QUESTION, BUTTONS_OK_CANCEL, Entry, BUTTONS_OK, \
    FileChooserDialog, FILE_CHOOSER_ACTION_SAVE, STOCK_CANCEL, \
    RESPONSE_CANCEL, STOCK_SAVE, RESPONSE_OK, DIALOG_MODAL

from datetime import datetime

from bokeep.plugins.trust.GUIs.management.trustor_transactions import trustor_transactions

from os.path import abspath, dirname, join, exists

class trustor_management(object):
    def __init__(self, trust_module, parent_window, backend_account_fetch):
        self.backend_account_fetch = backend_account_fetch
        self.trust_module = trust_module
        self.trustors = self.trust_module.get_trustors()
        self.current_name = None

        self.init()
        if parent_window != None:
            self.top_window.set_transient_for(parent_window)
            self.top_window.set_modal(True)

        self.extended_init()
        if hasattr(self.trust_module, 'trust_liability_account_str'):
            self.widgets['trust_liability_account_label'].set_text(
                self.trust_module.trust_liability_account_str)
        if hasattr(self.trust_module, 'cash_account_str'):
            self.widgets['cash_account_label'].set_text(
                self.trust_module.cash_account_str )
        self.widgets['currency_text_entry'].set_text(
            self.trust_module.get_currency() )
            
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
        
        self.trustor_view = self.widgets['trustor_view']

        self.refresh_trustor_list()

    def init(self):
        filename = 'data/trustor_management.glade'
        top_window = 'TrustManagement'
        do_OldGladeWindowStyleConnect(
            self, self.construct_filename(filename), top_window)

    def on_add_button_clicked(self, *args):
        # Ask the user for a new trustor's name.
        md = MessageDialog(parent = self.top_window,
                           type = MESSAGE_QUESTION,
                           buttons = BUTTONS_OK_CANCEL,
                           message_format = "What's the new trustor's name?")
        vbox = md.get_child()
        name_entry = Entry()
        vbox.pack_end(name_entry)
        vbox.show_all()
        r = md.run()
        new_trustor_name = name_entry.get_text()
        md.destroy() # destroys embedded widgets too
        
        # Save the new trustor.
        if r == RESPONSE_OK and new_trustor_name != '':
            self.current_name = new_trustor_name
            self.trust_module.add_trustor_by_name(new_trustor_name)
            transaction.get().commit()
            self.refresh_trustor_list()

    def on_remove_button_clicked(self, *args):
        trustor = self.trust_module.get_trustor(self.current_name)

        if len(trustor.transactions) > 0:
            cantDeleteDia = MessageDialog(
                flags = DIALOG_MODAL,
                message_format = 'Cannot delete, trustor has associated transacactions.',
                buttons = BUTTONS_OK)
            cantDeleteDia.run()
            cantDeleteDia.hide()
        else:            
            self.trust_module.drop_trustor_by_name(self.current_name)
            transaction.get().commit()
            
            # Update the view.
            self.widgets['remove_button'].set_sensitive(False)
            self.widgets['details_button'].set_sensitive(False)
            self.refresh_trustor_list()

    def on_details_button_clicked(self, *args):
        if self.current_name != None:
            trustor = self.trust_module.get_trustor(self.current_name)
            trans = trustor_transactions(self.trust_module, trustor, self)

    def set_trustor(self, trustor_selected):
        trustor = self.trust_module.get_trustor(trustor_selected)
        self.current_name = trustor.name

    def on_trustor_view_cursor_changed(self, *args):
        sel = self.trustor_view.get_selection()
        sel_iter = sel.get_selected()[1]
        if sel_iter != None: # If the user clicked a row as opposed to whitespace...
            sel_row = self.trustor_list[sel_iter]
            trustor_selected = sel_row[0]
            self.set_trustor(trustor_selected)
        
        # Update the view.
        self.widgets['remove_button'].set_sensitive(True)
        self.widgets['details_button'].set_sensitive(True)

    def generate_balance_report(self, filename):
        report_file = open(filename, 'w')
        now = datetime.today()
        nowstring = now.strftime("%B %d, %Y, %H:%M")
        report_file.write("Trustor balance report as at " + nowstring + "\n\n")
        for trustor in self.trustors:
            report_file.write(trustor + ' ' + str(self.trustors[trustor].get_balance()) + '\n')

        report_file.close()

    def on_report_button_clicked(self, *args):
        fcd = FileChooserDialog("Choose report file and location",
                                None,
                                FILE_CHOOSER_ACTION_SAVE,
                                (STOCK_CANCEL, RESPONSE_CANCEL,
                                    STOCK_SAVE, RESPONSE_OK))
        fcd.set_modal(True)
        result = fcd.run()
        file_path = fcd.get_filename()
        fcd.destroy()
        if result == RESPONSE_OK and file_path != None:
            self.generate_balance_report(file_path)

    def handle_account_fetch(self, label, setter):
        account_spec, account_str = self.backend_account_fetch(
            self.top_window)
        if account_spec != None:
            setter(account_spec, account_str)
            label.set_text(account_str)
    
    def on_select_trust_liability_clicked(self, *args):
        self.handle_account_fetch(
            self.widgets['trust_liability_account_label'],
            self.trust_module.set_trust_liability_account )
    
    def on_select_cash_account_clicked(self, *args):
        self.handle_account_fetch(
            self.widgets['cash_account_label'],
            self.trust_module.set_cash_account )
    
    def currency_text_entry_changed(self, *args):
        self.trust_module.currency = \
            self.widgets['currency_text_entry'].get_text()
        transaction.get().commit()