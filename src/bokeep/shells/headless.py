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

# python
from optparse import OptionParser
from os.path import dirname, abspath, join, exists
from sys import path

# gtk imports
import gtk
from gtk import Window, Label, main_quit

# bokeep imports
# important to do after the path adjustment above
from bokeep.util import null_function

from bokeep.config import \
    get_bokeep_config_paths, \
    get_bokeep_bookset_from_config, get_bokeep_configuration, \
    BoKeepConfigurationFileException, BoKeepConfigurationDatabaseException, \
    get_plugins_directories_from_config

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
    window = cbargs[0]
    return get_bokeep_bookset_from_config(config_path, config)


def bokeep_main():
    def bookset_startup_once_config_established(
        config_path, config, config_approved_func, bookset_approved_func, e, *cbargs):
        config_approved_func(config_path, config)
        __initialize_plugin_directories(config, config_path)
        bookset = shell_startup_bookset_fetch(config_path, config, e, *cbargs)
        bookset_ok = bookset != None
        if bookset_ok:
            bookset_approved_func(bookset)
        return bookset_ok

    op = OptionParser()
    op.add_option("-c", "--config", dest="configfile",
                  default=None,
                  help="specify configuration file" )
    (options, args) = op.parse_args()

    config_path = get_bokeep_config_paths(options.configfile)[0]
    
    # default state until we've successfully loaded them
    config = None
    bookset = None
    try:
        config = get_bokeep_configuration(config_path)
        bookset = get_bokeep_bookset_from_config(config_path, config)
    except BoKeepConfigurationFileException, e:
        def startup_callback(config_path, config, config_approved_func,
                             bookset_approved_func, *cbargs):
            config_path, config = shell_startup_config_establish(config_path, e, *cbargs)
            if config_path == None or config == None:
                return False
            else:
                return bookset_startup_once_config_established(
                    config_path, config, config_approved_func, bookset_approved_func,
                    None, *cbargs)

    except BoKeepConfigurationDatabaseException, e:
        def startup_callback(config_path, config, config_approved_func,
                             bookset_approved_func, *cbargs):
             if config == None or config_path == None:
                 return False
             else:
                 return bookset_startup_once_config_established(
                     config_path, config, config_approved_func, bookset_approved_func,
                     e, *cbargs)
    else:
        __initialize_plugin_directories(config, config_path)

        startup_callback = lambda *args, **kargs: True

    # we call this here instead of in either of the two except clauses or else clause
    # so we can get rid of the exception handling stack frame, because whichever function
    # this it, it probably blocks for a long, long time...
    shell_startup(config_path, config, bookset, startup_callback,
                  options, args)

# Add the plugin directories from the configuration to the program's path.
def __initialize_plugin_directories(config, config_path):
	for plugin_directory in get_plugins_directories_from_config(config, config_path):
		path.append(plugin_directory)

if __name__ == "__main__":
    bokeep_main() # should really look at return value and set exit status
