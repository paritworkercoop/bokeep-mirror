#!/usr/bin/env python
    
#----------------------------------------------------------------------
# trustor_management.py
# Dave Reed
# 08/06/2010
#----------------------------------------------------------------------

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

from GladeWindow import *

#----------------------------------------------------------------------

class trustor_management(GladeWindow):

    #----------------------------------------------------------------------

    def __init__(self):

        self.bookset = BoKeepBookSet( get_database_cfg_file() )
        self.book = self.bookset.get_book('testbook')
        self.backend = self.book.get_backend_module()
        self.trust_module = self.book.get_module('bokeep.modules.trust')
        self.trustors = self.trust_module.get_trustors()
        print 'current trustors: ' + str(self.trustors)

        ''' '''
        
        self.init()

    #----------------------------------------------------------------------

    def init(self):

        filename = 'trustor_management.glade'

        widget_list = [
            'TrustManagement',
            'add_button',
            'delete_button',
            'zoom_button',
            'name_entry',
            'save_button',
            ]

        handlers = [
            'on_window_destroy',
            'on_add_button_clicked',
            'on_delete_button_clicked',
            'on_zoom_button_clicked',
            'on_save_button_clicked',
            ]

        top_window = 'TrustManagement'
        GladeWindow.__init__(self, filename, top_window, widget_list, handlers)
    #----------------------------------------------------------------------

    def on_add_button_clicked(self, *args):
        print 'add button clicked'

    #----------------------------------------------------------------------

    def on_delete_button_clicked(self, *args):
        print 'delete button clicked'

    #----------------------------------------------------------------------

    def on_zoom_button_clicked(self, *args):
        print 'zoom button clicked'

    #----------------------------------------------------------------------

    def on_save_button_clicked(self, *args):
        print 'save button clicked'

#----------------------------------------------------------------------

def main(argv):

    w = trustor_management()
    w.show()
    gtk.main()

#----------------------------------------------------------------------

if __name__ == '__main__':
    main(sys.argv)
