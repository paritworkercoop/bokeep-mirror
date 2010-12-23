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

from bokeep.gui.gladesupport.GladeWindow import GladeWindow

from gtk import ListStore

from decimal import Decimal, InvalidOperation
from datetime import date

class mileage_entry(GladeWindow):
    def __init__(self, trans, transid, plugin, gui_parent,
                 change_register_function):
        from plugin import get_mileage_glade_file
        self.gui_built = False
        GladeWindow.__init__(
            self, get_mileage_glade_file(),
            'window1', ('window1', 'amount_entry', 'vbox1', 'calendar1'),
            ('on_window_destroy', 'on_amount_entry_changed',
             'on_cal_date_changed') )

        self.trans = trans
        self.widgets['calendar1'].select_month(
            self.trans.trans_date.month-1, self.trans.trans_date.year)
        self.widgets['calendar1'].select_day(self.trans.trans_date.day)
        
        if isinstance(self.trans.get_distance(), Decimal):
            self.widgets['amount_entry'].set_text(
                str(self.trans.get_distance()) )

        self.plugin = plugin
        self.change_register_function = change_register_function
        
        if not gui_parent == None:
            self.widgets['vbox1'].reparent(gui_parent)
        self.top_window.hide()
        self.gui_built = True

    def detach(self):
        self.widgets['vbox1'].reparent(self.top_window)

    def on_amount_entry_changed(self, *args):
        # skip this if being set by code and not user at init
        if not self.gui_built: return
        try:
            self.trans.set_distance(
                Decimal(self.widgets['amount_entry'].get_text()))
        except InvalidOperation: pass
        else:
            self.change_register_function()

    def on_cal_date_changed(self, *args):
        # skip this if being set by code and not user at init
        if not self.gui_built: return
        (year, month, day) = self.widgets['calendar1'].get_date()
        self.trans.trans_date = \
            date(year, month+1, day)
        self.change_register_function()
       
