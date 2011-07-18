# Technically this file has python "code", but the intent is to just be
# configuration data you can load and use with the multipage glade plugin
#
# Unlimited redistribution and modification of this file is permitted
# Original author: ParIT Worker Co-operative <paritinfo@parit.ca>
# You may remove this notice from this file.

# python imports
from decimal import Decimal
from datetime import date

#force_crc_backwards_config = None

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
    return crc in (236918719, 914482147, 1328275852, 1642840702, 2135928719, 2362158402,
                   2593818192, 3185835452, 2668236786,)

def post_module_load_hook(transaction, plugin, config_module):
    print 'post_module_load_hook'

def initialization_hook(plugin_edit_instance, transaction, plugin, book):
    print 'initialization hook'

def page_change_acceptable(old_page, new_page):
    print 'did page change acceptability check', old_page, 'to', new_page
    return True

def page_pre_change_config_hooks(old_page, new_page):
    print 'pre-change hook, going from', old_page, 'to', new_page

def page_post_change_config_hooks(old_page, new_page):
    print 'post-change hook, went from', old_page, 'to', new_page

non_decimal_check_labels = ( (P1, 'name_entry'), )

blanks_are_fine_for_decimal_coversion_treat_as_zero = (
    (P1, 'entry1'), )

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
