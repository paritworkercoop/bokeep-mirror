#!/usr/bin/env python

# python imports
from optparse import OptionParser
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

from trustor_entry import trustor_entry

import gtk

def run_edit_or_new_gui(trans_id, trust_trans, trust_module):
    # the code here is basically going to be, setup gtk gui, run gtk main()
    # do any cleanup after gtk main is done()
#    trust_trans.transfer_amount = Decimal(raw_input("> "))
    enter = trustor_entry(trust_trans, trust_module, True)
    enter.show()
    gtk.main()

#    enter.transfer_amount = enter.get_transfer_amount()

def view_only_gui(trans_id, trust_trans, trust_module):
    enter = trustor_entry(trust_trans, trust_module, False)
    enter.show()
    gtk.main()


def print_trans_error(backend, trans_id):
    if not backend.transaction_is_clean(trans_id):
        sys.stderr.write("%s is not clean, error\n%s\n" % 
                         backend.reason_transaction_is_dirty(trans_id))

def trust_in_out_main():
    parser = OptionParser()
    parser.add_option("-b", "--book", dest="book",
                      default="testbook", help="specify which bokeep book")
    parser.add_option("-u", "--update", dest="update",
                      default=False, action="store_true",
                      help="specify a transaction being updated")
    parser.add_option("-v", "--view-only", dest="viewonly",
                      default=False, action="store_true",
                      help="specify a transaction should be viewed only")
    parser.add_option("-i", "--id", dest="id",
                      default=None,
                      help="specify a transaction id if updating or deleting")
    parser.add_option("-r", "--remove", dest="remove", default=False,
                      action="store_true",
                      help="specify a transaction is being removed")
    parser.add_option("-l", "--list", dest="list", default=False,
                      action="store_true")
    parser.add_option("-o", "--out", dest="out", default=False,
                     action="store_true")
    (options, args) = parser.parse_args()

    bookset = BoKeepBookSet( get_database_cfg_file() )
    book = bookset.get_book(options.book)
    backend = book.get_backend_module()
    trust_module = book.get_module('bokeep.modules.trust')

    if options.update:
        assert( options.id != None )
        trans_id = int(options.id)
        trust_trans = book.get_transaction(trans_id)
        if options.viewonly:
            view_only_gui(trans_id, trust_trans, trust_module)
        else:
            run_edit_or_new_gui(trans_id, trust_trans, trust_module)
    elif options.remove:
        assert( options.id != None )
        trans_id = int(options.id)
        trust_module.remove_transaction(trans_id)
        book.remove_transaction(trans_id)
        # the above is doing this
        #backend.mark_transaction_for_removal(id)
        backend.flush_backend()
        try:
            print_trans_error(backend, trans_id)
        except BoKeepBackendException, e:
            # we're actually expecting this if the remove was a success
            if e.message != "A transaction must exist to be considered clean":
                raise e
        backend.close()
        transaction.get().commit()
        return # exit early
    elif options.list:
        for trans_id, trust_trans in book.trans_tree.iteritems():
            if isinstance(trust_trans, TrustTransaction):
                print trans_id, backend.transaction_is_clean(trans_id), \
                    trust_trans.get_transfer_amount()
        backend.close()
        return # exit early

    else: # new
        if options.out:
            trust_trans = TrustMoneyOutTransaction()
        else:
            trust_trans = TrustMoneyInTransaction()
        trans_id = book.insert_transaction(trust_trans)
        trust_module.register_transaction(trans_id, trust_trans)
        print "new transaction is is", trans_id
        run_edit_or_new_gui(trans_id, trust_trans, trust_module)

    transaction.get().commit()
    backend.mark_transaction_dirty(trans_id, trust_trans)
    backend.flush_backend()
    transaction.get().commit()
    backend.close()

    print_trans_error(backend, trans_id)
    
if __name__ == "__main__":
    trust_in_out_main()
        
