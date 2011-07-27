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

# bokeep imports
# important to do after the path adjustment above
from bokeep.util import null_function

def shell_startup(config_path, config, bookset, startup_callback,
                  cmdline_options, cmdline_args):
    window = Window()

    def window_startup_event_handler(*args):
        if not startup_callback(
            config_path, config,
            null_function, null_function, 
            window):
            main_quit()
        window.disconnect(window_connection)

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

