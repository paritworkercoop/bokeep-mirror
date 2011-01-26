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
#!/usr/bin/env python

from bokeep.gui.gladesupport.glade_util import \
    do_OldGladeWindowStyleConnect

# ZOPEDB imports
import transaction

from gtk import ListStore

from decimal import Decimal

from os.path import abspath, dirname, join, exists

from bokeep.plugins.trust import \
    TrustTransaction, TrustMoneyInTransaction, TrustMoneyOutTransaction

class trustor_entry(object):
    def __init__(self, trust_trans, trans_id, trust_module, gui_parent,
                 editable, change_register_function):
        self.change_register_function = change_register_function
        self.gui_built = False
        self.trust_trans = trust_trans 
        self.trans_id = trans_id
        self.trust_module = trust_module
        self.trustors = self.trust_module.get_trustors()
        self.editable = editable
        self.trans_trustor = self.trust_trans.get_trustor()

        self.init()
        self.extended_init()

        if not gui_parent == None:
            self.widgets['vbox1'].reparent(gui_parent)
        self.top_window.hide()
        self.gui_built = True

    def detach(self):
        self.widgets['vbox1'].reparent(self.top_window)

    def extended_init(self):
        self.trustor_combo = self.widgets['trustor_combo']
        self.trustor_list = ListStore( str )
        self.trustor_combo.set_model(self.trustor_list)
        index = 0
        use_index = -1
        for trustor in self.trustors:
            self.trustor_list.append([trustor])
            if not(self.trans_trustor == None) and self.trans_trustor.name == trustor:
                use_index = index
            index += 1
 
        if use_index > -1:
            self.trustor_combo.set_active(use_index)
            self.widgets['amount_entry'].set_text(str(self.trust_trans.get_displayable_amount()))
        else:
            self.trustor_combo.set_active(0)

        if not self.editable:
            self.widgets['amount_entry'].set_sensitive(False)


    def construct_filename(self, filename):
        import trustor_entry as trust_module
        return join( dirname( abspath( trust_module.__file__ ) ),
                              filename)
        
    def init(self):

        filename = 'data/trustor_entry.glade'
        top_window = 'window1'
        do_OldGladeWindowStyleConnect(
            self, self.construct_filename(filename), top_window)


    def update_trans(self):
        entered_amount = self.widgets['amount_entry'].get_text()

        if entered_amount == '':
            print 'setting amount to zero'
            self.trust_trans.transfer_amount = Decimal('0')
        else:
            print 'using ' + entered_amount + ' for amount'
            self.trust_trans.transfer_amount = Decimal(entered_amount)

        print self.trust_trans.get_displayable_amount()
        self.change_register_function()
        trustor = self.trust_module.get_trustor(self.widgets['trustor_combo'].get_active_text())
        self.trust_module.associate_transaction_with_trustor(self.trans_id, self.trust_trans, trustor.name)

    def on_window_destroy(self, *args):
        if self.editable:
            self.update_trans()
        gtk.main_quit()

    def on_trustor_combo_changed(self, *args):
        if self.gui_built:
            self.update_trans()

    def on_amount_entry_changed(self, *args): 
        if self.gui_built:
            self.update_trans()

