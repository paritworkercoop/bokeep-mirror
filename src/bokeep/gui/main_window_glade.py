# Copyright (C) 2010  ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
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
# Author: Mark Jenkins <mark@parit.ca>

# python imports
from os.path import abspath, dirname, join

def get_this_module_file_path():
    """Returns the filename of this code file."""
    
    import main_window_glade as main_window_glade_module
    return main_window_glade_module.__file__

def get_main_window_glade_file():
    """Returns the filename of the main window."""
    
    return join( dirname( abspath(get_this_module_file_path() ) ),
                 'bokeep_main_window.glade' )
