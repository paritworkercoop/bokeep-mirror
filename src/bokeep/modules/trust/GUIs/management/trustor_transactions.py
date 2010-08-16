#!/usr/bin/env python
    
#----------------------------------------------------------------------
# trustor_transactions.py
# Dave Reed
# 08/10/2010
#----------------------------------------------------------------------

import sys

from GladeWindow import *

from gtk import ListStore, TreeViewColumn, CellRendererText
from bokeep.modules.trust import \
    TrustMoneyInTransaction, TrustMoneyOutTransaction

from datetime import datetime

from os.path import abspath, dirname, join, exists

#----------------------------------------------------------------------

class trustor_transactions(GladeWindow):
    def construct_filename(self, filename):
        import trustor_management as trust_module
        return join( dirname( abspath( trust_module.__file__ ) ),
                              filename)

    #----------------------------------------------------------------------

    def __init__(self, trustor):

        self.trustor = trustor

        ''' '''
        
        self.init()
        self.extended_init()

    #----------------------------------------------------------------------

    def get_tran_type(self, transaction):
        if isinstance(transaction, TrustMoneyInTransaction):
            return 'In'
        elif isinstance(transaction, TrustMoneyOutTransaction):
            return 'Out'
        else:
            return 'unknown'

    def extended_init(self):
        self.add_widgets('transactions_view', 'dyn_name', 'dyn_balance')
 
        self.widgets['dyn_name'].set_text(self.trustor.name)
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

        widget_list = [
            'window1',
            'report_button',
            ]

        handlers = [
            'on_report_button_clicked',
            ]

        top_window = 'window1'
        GladeWindow.__init__(self, self.construct_filename(filename), top_window, widget_list, handlers)
    #----------------------------------------------------------------------

    def generate_transaction_report(self, filename):
        report_file = open(filename, 'w')
        now = datetime.today()
        nowstring = now.strftime("%B %d, %Y, %H:%M")
        report_file.write("Trustor transaction report for " + self.trustor.name + " as at " + nowstring + "\n\n")

        for transaction in self.trustor.transactions:
            report_file.write(transaction.trans_date.strftime("%B %d, %Y, %H:%M") + ' ' + self.get_tran_type(transaction) + ' ' + str(transaction.get_transfer_amount()) + '\n')

        report_file.write('\ncurrent balance: ' + str(self.trustor.get_balance()) + '\n')
        report_file.close()

    def on_report_button_clicked(self, *args):
        filesel = gtk.FileSelection(title="Choose report file and location")
        filesel.run()        
        filename = filesel.get_filename()
        filesel.hide()
        self.generate_transaction_report(filename)


    


#----------------------------------------------------------------------

def main(argv):

    w = trustor_transactions()
    w.show()
    gtk.main()

#----------------------------------------------------------------------

if __name__ == '__main__':
    main(sys.argv)
