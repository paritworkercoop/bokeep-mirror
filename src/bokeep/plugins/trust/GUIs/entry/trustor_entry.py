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

from bokeep.gui.gladesupport.glade_util import \
    load_glade_file_get_widgets_and_connect_signals

# ZOPEDB imports
import transaction

from gtk import ListStore, TextBuffer, main_quit

from decimal import Decimal, InvalidOperation

from os.path import abspath, dirname, join, exists

from bokeep.plugins.trust import \
    TrustTransaction, TrustMoneyInTransaction, TrustMoneyOutTransaction
    
from bokeep.util import get_file_in_same_dir_as_module

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

        import trustor_entry as plugin_mod
        filename = get_file_in_same_dir_as_module(plugin_mod,
                                                  'data/trustor_entry.glade')
        load_glade_file_get_widgets_and_connect_signals(
            glade_file = filename,
            root_widget = 'window1',
            widget_holder = self,
            signal_recipient = self)
        self.extended_init()

        if not gui_parent == None:
            self.table.reparent(gui_parent)

        buff = self.description_textview.get_buffer()
        buff.connect("changed", self.description_changed, None)

        self.window1.hide()
        self.gui_built = True
        
        self.update_trans() # save new transaction immediately after creation

    def description_changed(self, textbuffer, args):
        if self.gui_built:
            self.update_trans()

    def detach(self):
        self.table.reparent(self.window1)

    def extended_init(self):
        self.trustor_list = ListStore( str )
        self.trustor_combo.set_model(self.trustor_list)
        index = 0
        use_index = -1
        for trustor_name in self.trustors:
            self.trustor_list.append([trustor_name])
            if not(self.trans_trustor == None) and self.trans_trustor.name == trustor_name:
                use_index = index
            index += 1
 
        if use_index > -1:
            self.trustor_combo.set_active(use_index)
            self.amount_entry.set_text(str(self.trust_trans.get_displayable_amount()))
            self.description_textview.get_buffer().set_text(str(self.trust_trans.get_memo()))
        else:
            self.trustor_combo.set_active(0)

        trans_date = self.trust_trans.trans_date
        self.entry_date_label.set_text(
                "%s-%s-%s" %
                (trans_date.year, trans_date.month, trans_date.day) )


        if not self.editable or self.trust_trans.get_trustor() == None :
            self.amount_entry.set_sensitive(False)


    def construct_filename(self, filename):
        import trustor_entry as trust_module
        return join( dirname( abspath( trust_module.__file__ ) ),
                              filename)

    def update_trans(self):
        entered_amount = self.amount_entry.get_text()

        try:
            self.trust_trans.transfer_amount = Decimal(entered_amount)
        except InvalidOperation:
            # In case the user has entered something like "" or ".".
            self.trust_trans.transfer_amount = Decimal('0')

        textbuff = self.description_textview.get_buffer()
        entered_description = textbuff.get_text(textbuff.get_start_iter(), textbuff.get_end_iter())

        self.trust_trans.memo = entered_description

        self.change_register_function()
        trustor = self.trust_module.get_trustor(self.trustor_combo.get_active_text())

        if not(trustor == None):
            self.trust_module.associate_transaction_with_trustor(self.trans_id, self.trust_trans, trustor.name)

    def on_window_destroy(self, *args):
        if self.editable:
            self.update_trans()
        main_quit()

    def on_trustor_combo_changed(self, *args):
        if self.gui_built:
            self.update_trans()

    def on_amount_entry_changed(self, *args): 
        if self.gui_built:
            self.update_trans()

