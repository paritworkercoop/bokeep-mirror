# Technically this file has python "code", but the intent is to just be
# configuration data you can load and use with the multipage glade plugin
#
# Unlimited redistribution and modification of this file is permitted
# Original author: ParIT Worker Co-operative <paritinfo@parit.ca>
# You may remove this notice from this file.

# python imports
from decimal import Decimal
from datetime import date

# bokeep imports
from bokeep.plugins.multipageglade import \
    make_sum_entry_val_func, make_get_entry_val_func, \
    make_get_cal_grab_function
from bokeep.util import get_file_in_same_dir_as_module

def get_this_mod():
    import multipageglade_configuration
    return multipageglade_configuration

GLADE_FILE = get_file_in_same_dir_as_module(
    get_this_mod(), 'multipageexample.glade')
P1 = (GLADE_FILE, "window1")
P2 = (GLADE_FILE, "window2")

A1 = ("Assets",)
A2 = ("Liabilities",)

# all variables below here are the ones the plugin is going to search for
pages = (P1, P2)

get_currency = lambda *args: "CAD"
get_description = lambda *args: "example glade prog"

# should replace these with fetching an example name field
get_chequenum = lambda *args: 1
get_trans_date = make_get_cal_grab_function(P1, "calendar1")

def backwards_config_support(crc):
    return crc in (3185835452, 2668236786,)

def page_change_acceptable(old_page, new_page):
    print 'did page change acceptability check', old_page, 'to', new_page
    return True

auto_update_labels = (
    (P1, 'label1', make_get_entry_val_func(P1, "entry1") ),
    (P2, "label2",
     make_sum_entry_val_func( (
                make_get_entry_val_func(P1, "entry1"),
                make_get_entry_val_func(P2, "entry2") ), () ) ),
    )

fin_trans_template = (
    # DEBITS
    ( ("did you get my memo",
       make_get_entry_val_func(P1, "entry1"), A1), # end trans_line tuple
      ("you're reading this right",
       make_get_entry_val_func(P2, "entry2"), A1), # end trans_line tuple
      ), # DEBITS

    # CREDITS
    ( ("this one is almost pointless", make_sum_entry_val_func(
            ( make_get_entry_val_func(P1, "entry1"),
              lambda *args: Decimal(1),
              ), # end positive tuple
            ( make_get_entry_val_func(P1, "entry1"), ) # end negative tuple
            ), # make_sum_entry_val_func
       A2), # end credit tuple
      ("and this once cancels the debits and pointless",
       make_sum_entry_val_func(
                (make_get_entry_val_func(P1, "entry1"),
                 make_get_entry_val_func(P2, "entry2")), # end positive tuple
                ( lambda *args: Decimal(1), ),
                ),
       A2), # end credit tuple
      ) # CREDITS
    ) # fin_trans_template
