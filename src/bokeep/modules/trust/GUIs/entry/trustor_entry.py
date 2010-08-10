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

    def __init__(self, trust_trans, trust_module):

        self.trust_trans = trust_trans 
        self.trust_module = trust_module
        self.trustors = self.trust_module.get_trustors()

        ''' '''
        
        self.init()
        self.extended_init()


    #----------------------------------------------------------------------

    def extended_init(self):
        self.add_widgets('trustor_combo')
        self.trustor_combo = self.widgets['trustor_combo']
        self.trustor_list = ListStore( str )
        self.trustor_combo.set_model(self.trustor_list)
        for trustor in self.trustors:
            self.trustor_list.append([trustor])
 
        self.trustor_combo.set_active(0)


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


    def on_window_destroy(self, *args):
        self.trust_trans.transfer_amount = Decimal(self.widgets['amount_entry'].get_text())
        trustor = self.trust_module.get_trustor(self.widgets['trustor_combo'].get_active_text())
        trustor.add_transaction(self.trust_trans)
        print 'current transactions for ' + str(trustor) + ': ' + str(trustor.transactions)
        GladeWindow.on_window_destroy(self, *args)

#----------------------------------------------------------------------

def main(argv):

    w = trustor_entry()
    w.show()
    gtk.main()

#----------------------------------------------------------------------

if __name__ == '__main__':
    main(sys.argv)
