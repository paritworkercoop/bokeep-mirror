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
# Authors: Jamie Campbell <jamie@parit.ca>, Mark Jenkins <mark@parit.ca>
    
# python imports
from decimal import Decimal

# zopedb imports
import transaction

# bo-keep imports
from bokeep.plugins.trust import \
    TrustTransaction, TrustMoneyInTransaction, TrustMoneyOutTransaction
from bokeep.backend_plugins.module import BoKeepBackendException

from bokeep.gui.gladesupport.GladeWindow import GladeWindow

from gtk import ListStore, TreeViewColumn, CellRendererText, MessageDialog
import gtk

from datetime import datetime

from bokeep.plugins.trust.GUIs.management.trustor_transactions import trustor_transactions

from os.path import abspath, dirname, join, exists

class trustor_management(GladeWindow):
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
            'trust_liability_account_label',
            'cash_account_label',
            ]

        handlers = [
            'on_window_destroy',
            'on_add_button_clicked',
            'on_delete_button_clicked',
            'on_trustor_view_cursor_changed',
            'on_zoom_button_clicked',
            'on_save_button_clicked',
            'on_report_button_clicked',
            'on_select_trust_liability_clicked',
            'on_select_cash_account_clicked',
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
            transaction.get().commit()
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
            transaction.get().commit()
            self.refresh_trustor_list()
            trustor_name = self.widgets['name_entry'].set_text('')
        else:
            #we're updating the name of someone who already exists
            new_name = self.widgets['name_entry'].get_text()
            self.trust_module.rename_trustor(self.current_name, new_name)
            transaction.get().commit()
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
        



    
