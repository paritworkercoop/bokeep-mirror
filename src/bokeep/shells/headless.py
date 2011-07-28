# Copyright (C) 2011  ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
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
# Authors: Mark Jenkins <mark@parit.ca>

# gtk imports
import gtk
from gtk import Window, Label, main_quit, VBox

# zodb imports
from persistent import Persistent
import transaction

# bokeep imports
# important to do after the path adjustment above
from bokeep.util import null_function, do_module_import
from bokeep.shells import \
    (GUI_STATE_SUB_DB,
     TRANSACTION_ALL_EDIT_FIRST_TIME_HEADLESS,
     TRANSACTION_ALL_EDIT_HEADLESS)
from bokeep.gui.state import \
    instantiate_transaction_class_add_to_book_backend_and_plugin

HEADLESS_STATE_SUB_DB = 'headless_state'

class HeadlessShellState(Persistent):
    def __init__(self):
        self.set_no_current_transaction()

    def set_no_current_transaction(self):
        self.current_transaction_id = None

PLUGIN_ARGUMENT, TRANSACTION_TYPE_CODE = range(2)

def shell_startup(config_path, config, bookset, startup_callback,
                  cmdline_options, cmdline_args):
    window = Window()

    def window_startup_event_handler(*args):
        db_handle = bookset.get_dbhandle()
        plugin_name = cmdline_args[PLUGIN_ARGUMENT]

        if ( not startup_callback(
                config_path, config,
                null_function, null_function, 
                window) or 
             not db_handle.has_sub_database(GUI_STATE_SUB_DB) or
             len(cmdline_args) < 0
            ):
            main_quit()
        
        window.disconnect(window_connection)
        guistate = db_handle.get_sub_database(GUI_STATE_SUB_DB)
        book = guistate.get_book()

        if (book == None or
            not book.has_enabled_frontend_plugin(plugin_name) ):
            main_quit()

        headless_state = db_handle.get_sub_database_do_cls_init(
            HEADLESS_STATE_SUB_DB, HeadlessShellState)

        plugin = book.get_frontend_plugin(plugin_name)
        
        transaction_type_codes = tuple(plugin.get_transaction_type_codes())

        if len(transaction_type_codes) == 0:
            main_quit()

        if (headless_state.current_transaction_id == None or
            not plugin.has_transaction(headless_state.current_transaction_id)):
            # check above is important because we sub index
            # transaction_type_codes
            type_code = (transaction_type_codes[0] if len(cmdline_args) == 1
                         else int(cmdline_args[TRANSACTION_TYPE_CODE_POS_ARG]) )

            # if the user specifies a type code, it better be an available one
            # should convert this to a warning some day
            if type_code not in transaction_type_codes:
                main_quit()

            transaction_id, bokeep_transaction = \
                instantiate_transaction_class_add_to_book_backend_and_plugin(
                plugin.get_transaction_type_from_code(type_code),
                plugin,
                book)
            headless_state.current_transaction_id = transaction_id
            display_mode = TRANSACTION_ALL_EDIT_FIRST_TIME_HEADLESS
            transaction.get().commit()
        else:
            bokeep_transaction = book.get_transaction(
                headless_state.current_transaction_id)

            # go through all the transaction type codes for this plugin
            # and find one that provides class that matches the
            # class of the existing transaction
            #
            # if none of them match (how could that happen, bad error!)
            # we quit
            #
            # the implementation of the linear search is done as a generator
            # expression filtered on what we're searching for
            # by trying to iterate over that generator (.next()) we
            # find out if anything matches because StopIteration is
            # raised if nothing matches
            # but we also manage to stop the iteration early when something
            # does match
            #
            # yes, all this in the avoidance of doing some kind of
            # imperitive loop with a break statement and some kind of
            # check condition after... 
            try:
                type_code = (
                    type_code_test
                    for type_code_test in transaction_type_codes
                    if (plugin.get_transaction_type_from_code(type_code_test)
                        == bokeep_transaction.__class__)
                    ).next()

            except StopIteration:
                # should give an error msg
                main_quit()
            
            display_mode = TRANSACTION_ALL_EDIT_HEADLESS


        def change_register_function():
             book.get_backend_plugin().mark_transaction_dirty(
                headless_state.current_transaction_id, bokeep_transaction)

        def transaction_edit_finished_function():
            headless_state.set_no_current_transaction()
            transaction.get().commit()
            book.get_backend_plugin().flush_backend()
            # should change guistate (default shell persistent storage)
            # to be on this specific transid
            main_quit()

        window_vbox = VBox()
        window.add(window_vbox)
        display_hook = plugin.get_transaction_display_by_mode_hook(type_code)
        display_hook(bokeep_transaction,
                     headless_state.current_transaction_id,
                     plugin, window_vbox,
                     change_register_function, book,
                     display_mode, transaction_edit_finished_function)

        def window_close(*args):
            book.get_backend_plugin().flush_backend()
            main_quit()
        window.connect("delete_event", window_close)

        window.show_all()

    window_connection = window.connect(
        "window-state-event", window_startup_event_handler)

    window.show_all()
    gtk.main()

def shell_startup_config_establish(config_path, e, *cbargs):
    return None, None

def shell_startup_bookset_fetch(config_path, config, e, *cbargs):
    return None

