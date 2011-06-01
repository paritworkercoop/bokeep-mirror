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
# Author: Samuel Pauls <samuel@parit.ca>

from sys import path

from bokeep.config import get_bokeep_configuration, \
    get_plugins_directories_from_config, set_plugin_directories_in_config

class PluginDirectories:
    """Provides the logic of plugin directory management.  Storage and view
       responsibilities are managed elsewhere."""
    
    @staticmethod
    def initialize():
        """Should be called on program startup to make the plugins in the plugin
           directories available."""
        config = get_bokeep_configuration()
        plugin_directories = get_plugins_directories_from_config(config)
        for plugin_directory in plugin_directories:
            # Add the plugin directory to the program's PYTHONPATH so that
            # the plugins in it can be loaded.
            path.append(plugin_directory)

    # Removes the plugin directories from the PYTHONPATH so they are no longer
    # accessible to BoKeep.  Good to call before initializing a new batch.
    @staticmethod
    def change(new_plugin_directories):
        config = get_bokeep_configuration()
        
        # Erase the old list of plugin directories.
        plugin_directories = get_plugins_directories_from_config(config)
        for plugin_directory in plugin_directories:
            path.remove(plugin_directory)
        
        # Update the plugin directories configuration file for later BoKeep
        # sessions.
        plugin_directories = []
        for plugin_directory in new_plugin_directories:
            plugin_directories.append(plugin_directory)
        set_plugin_directories_in_config(config, plugin_directories)
        
        PluginDirectories.initialize()