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
from gtk import Window, Label, main_quit

# zodb imports
from persistent import Persistent

# bokeep imports
# important to do after the path adjustment above
from bokeep.util import null_function, do_module_import
from bokeep.shells import GUI_STATE_SUB_DB


HEADLESS_STATE_SUB_DB = 'headless_state'

class HeadlessShellState(Persistent):
    def __init__(self):
        # -1 instead of None because the transaction in
        # GUI_STATE_SUB_DB might be None and in that case the code down
        # below that does a comparison to determine if a new transaction
        # needs to be started still needs to reach that conclusion
        self.last_transaction_completed = -1

def shell_startup(config_path, config, bookset, startup_callback,
                  cmdline_options, cmdline_args):
    window = Window()

    def window_startup_event_handler(*args):
        db_handle = bookset.get_dbhandle()
        shell_plugin_name = cmdline_args[0]

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
        last_transaction_id = guistate.get_transaction_id()

        if (book == None or
            not book.has_enabled_frontend_plugin(shell_plugin_name) ):
            main_quit()

        headless_state = db_handle.get_sub_database_do_cls_init(
            HEADLESS_STATE_SUB_DB, HeadlessShellState)

        shell_plugin = book.get_frontend_plugin(shell_plugin_name)
        
        # cases where we're starting a new transaction
        if (not shell_plugin.has_transaction(last_transaction_id) or
            headless_state.last_transaction_completed == last_transaction_id):
            pass
        elif shell_plugin.has_transaction(transaction_id):
            pass
        # this should never happen, shell_plugin.has_transaction(transaction_id)
        # has to return True or False, so one of the above two cases should pass
        else:
            assert(False)

        window.add( Label(str(cmdline_args[0])))
        window.show_all()

    def window_close(*args):
        main_quit()

    window_connection = window.connect(
        "window-state-event", window_startup_event_handler)
    window.connect("delete_event", window_close)
    window.show_all()
    gtk.main()

def shell_startup_config_establish(config_path, e, *cbargs):
    return None, None

def shell_startup_bookset_fetch(config_path, config, e, *cbargs):
    return None

