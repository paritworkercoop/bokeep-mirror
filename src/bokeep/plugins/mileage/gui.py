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
import sys

from bokeep.gui.gladesupport import GladeWindow

from gtk import ListStore

from decimal import Decimal

from os.path import abspath, dirname, join, exists

class trustor_entry(GladeWindow):
    def detach(self):
        self.widgets['vbox1'].reparent(self.top_window)

    def __init__(self, mile_trans, trans_id, mile_plugin, gui_parent):

        self.gui_built = False
        
        self.init()

        if not gui_parent == None:
            self.widgets['vbox1'].reparent(gui_parent)
        self.top_window.hide()
        self.gui_built = True


    def construct_filename(self, filename):
        import trustor_entry as trust_module
        return join( dirname( abspath( trust_module.__file__ ) ),
                              filename)
        
    def init(self):

        filename = 'mileage.glade'

        widget_list = [
            'window1',
            ]

        handlers = [
            'on_window_destroy',
            ]

        top_window = 'window1'
        GladeWindow.__init__(self, self.construct_filename(filename), top_window, widget_list, handlers)


