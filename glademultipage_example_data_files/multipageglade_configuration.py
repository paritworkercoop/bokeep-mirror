# Technically this file has python "code", but the intent is to just be
# configuration data you can load and use with the multipage glade plugin
#
# Unlimited redistribution and modification of this file is permitted
# Original author: ParIT Worker Co-operative <paritinfo@parit.ca>
# You may remove this notice from this file.

from decimal import Decimal
from bokeep.plugins.multipageglade import \
    make_sum_entry_val_func, make_get_entry_val_func

P1 = "window1"
P2 = "window2"

PAGES = (P1, P2)
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
              lambda x: Decimal(1),
              ), # end positive tuple
            ( make_get_entry_val_func(P2, "entry2"), ) # end negative tuple
            ), # make_sum_entry_val_func
       A2), # end credit tuple
      ("and this once cancels the debits and pointless",
       make_sum_entry_val_func(
                (make_get_entry_val_func(P1, "entry1"),
                 make_get_entry_val_func(P2, "entry2")), # end positive tuple
                ( lambda x: Decimal(1), ),
                ),
       A2), # end credit tuple
      ) # CREDITS
    ) # fin_trans_template
