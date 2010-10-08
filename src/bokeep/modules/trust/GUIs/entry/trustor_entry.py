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

import sys

from bokeep.gui.gladesupport.GladeWindow import GladeWindow

# ZOPEDB imports
import transaction

from gtk import ListStore

from decimal import Decimal

from os.path import abspath, dirname, join, exists

from bokeep.modules.trust import \
    TrustTransaction, TrustMoneyInTransaction, TrustMoneyOutTransaction

from bokeep.book import BoKeepBookSet
from bokeep.config import get_database_cfg_file

class trustor_entry(GladeWindow):
    def __init__(self, trust_trans, trans_id, trust_module, gui_parent, editable):
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
        self.add_widgets('trustor_combo', 'vbox1')
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

        widget_list = [
            'window1',
            'amount_entry',
            ]

        handlers = [
            'on_window_destroy',
            'on_trustor_combo_changed',
            'on_amount_entry_changed',
            ]

        top_window = 'window1'
        GladeWindow.__init__(self, self.construct_filename(filename), top_window, widget_list, handlers)


    def update_trans(self):
        entered_amount = self.widgets['amount_entry'].get_text()

        if entered_amount == '':
            print 'setting amount to zero'
            self.trust_trans.transfer_amount = Decimal('0')
        else:
            print 'using ' + entered_amount + ' for amount'
            self.trust_trans.transfer_amount = Decimal(entered_amount)

        print self.trust_trans.get_displayable_amount()
        trustor = self.trust_module.get_trustor(self.widgets['trustor_combo'].get_active_text())
        self.trust_module.associate_transaction_with_trustor(self.trans_id, self.trust_trans, trustor.name)

    def on_window_destroy(self, *args):
        if self.editable:
            self.update_trans()
        GladeWindow.on_window_destroy(self, *args)

    def on_trustor_combo_changed(self, *args):
        if self.gui_built:
            self.update_trans()

    def on_amount_entry_changed(self, *args): 
        if self.gui_built:
            self.update_trans()

def main(argv):
    bookset = BoKeepBookSet( get_database_cfg_file() )
    book = bookset.get_book('testbook')
    trust_module = book.get_module('bokeep.modules.trust')

    trust_trans = TrustMoneyInTransaction()
    trans_id = book.insert_transaction(trust_trans)
    transaction.get().commit()
    w = trustor_entry(trust_trans, trans_id, trust_module, None, True)
    w.show()
    gtk.main()

if __name__ == '__main__':
    main(sys.argv)
