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
from gtk.glade import XML, get_widget_name

def load_glade_file_get_widgets_and_connect_signals(
    glade_file, root_widget, widget_holder=None, signal_recipiant=None ):
    glade_xml = XML(glade_file, root_widget)

    if signal_recipiant != None:
        glade_xml.signal_autoconnect( signal_recipiant )

    for widget in glade_xml.get_widget_prefix(""):
        setattr( widget_holder, get_widget_name(widget), widget )

