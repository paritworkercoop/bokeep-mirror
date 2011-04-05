# Technically this file has python "code", but the intent is to just be
# configuration data you can load and use with the multipage glade plugin
#
# Unlimited redistribution and modification of this file is permitted
# Original author: ParIT Worker Co-operative <paritinfo@parit.ca>
# You may remove this notice from this file.

from decimal import Decimal
from bokeep.plugins.multipageglade import \
    make_sum_entry_val_func, make_get_entry_val_func
from bokeep.util import get_file_in_same_dir_as_module

def get_this_mod():
    import multipageglade_configuration
    return multipageglade_configuration

GLADE_FILE = get_file_in_same_dir_as_module(
    get_this_mod(), 'multipageexample.glade')
P1 = (GLADE_FILE, "window1")
P2 = (GLADE_FILE, "window2")

pages = (P1, P2)
A1 = ("Assets,")
A2 = ("Liabilities,")

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
            ( make_get_entry_val_func(P2, "entry2"), ) # end negative tuple
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
