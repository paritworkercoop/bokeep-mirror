#!/usr/bin/env python
    
#----------------------------------------------------------------------
# trustor_entry.py
# Dave Reed
# 08/09/2010
#----------------------------------------------------------------------

import sys

from GladeWindow import *

from gtk import ListStore

from decimal import Decimal

#----------------------------------------------------------------------

class trustor_entry(GladeWindow):

    #----------------------------------------------------------------------

    def __init__(self, trust_trans, trust_module, editable):

        self.trust_trans = trust_trans 
        self.trust_module = trust_module
        self.trustors = self.trust_module.get_trustors()
        self.editable = editable
        self.trans_trustor = self.trust_trans.get_trustor()
        self.edit_trustor = True

        ''' '''
        
        self.init()
        self.extended_init()


    #----------------------------------------------------------------------

    def extended_init(self):
        self.add_widgets('trustor_combo')
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
            self.widgets['amount_entry'].set_text(str(self.trust_trans.get_transfer_amount()))
            self.trustor_combo.set_sensitive(False)
            self.edit_trustor = False
        else:
            self.trustor_combo.set_active(0)

        if not self.editable:
            self.widgets['amount_entry'].set_sensitive(False)


    def init(self):

        filename = 'trustor_entry.glade'

        widget_list = [
            'window1',
            'amount_entry',
            ]

        handlers = [
            'on_window_destroy',
            ]

        top_window = 'window1'
        GladeWindow.__init__(self, filename, top_window, widget_list, handlers)


    def update_trans(self):
        self.trust_trans.transfer_amount = Decimal(self.widgets['amount_entry'].get_text())
        trustor = self.trust_module.get_trustor(self.widgets['trustor_combo'].get_active_text())
        trustor.add_transaction(self.trust_trans)
        if self.edit_trustor:
            self.trust_trans.set_trustor(trustor)

    def on_window_destroy(self, *args):
        if self.editable:
            self.update_trans()
        GladeWindow.on_window_destroy(self, *args)

#----------------------------------------------------------------------

def main(argv):

    w = trustor_entry()
    w.show()
    gtk.main()

#----------------------------------------------------------------------

if __name__ == '__main__':
    main(sys.argv)
