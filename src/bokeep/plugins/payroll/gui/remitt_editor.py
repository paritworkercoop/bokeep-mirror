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
# Author: Mark Jenkins <mark@parit.ca>

# python import
from datetime import date

# bokeep imports
from bokeep.gui.gladesupport.glade_util import \
    load_glade_file_get_widgets_and_connect_signals
from bokeep.plugins.payroll.gui.config import get_payroll_glade_file

def convert_gtk_cal_date(cal):
    (year, month, day) = cal.get_date()
    return date(year, month+1, day)

def set_gtk_cal_to_date(cal, a_date):
    # keep in mind that any event handlers to for calendar changes will trigger
    # when you do this
    cal.select_month(a_date.month-1, a_date.year)
    cal.select_day(a_date.day)

class CanadianPayrollRemittEditor(object):
    def __init__(self, *args):
        self.gui_lock = True
        for i, key in enumerate(
            ('trans', 'transid', 'plugin', 'gui_parent',
             'change_register_function') ):
            setattr(self, key, args[i])

        load_glade_file_get_widgets_and_connect_signals(
            get_payroll_glade_file(),
            'window2', self, self)
        self.vbox1.reparent(self.gui_parent)
        self.window2.hide()       
        self.gui_lock = False

        # intentionally called after the gui lock is released because
        # these grab the gui lock for themselves it
        self.set_period_calendars()
        self.set_remit_date_calendar()

        # doesn't need the gui lock
        self.update_statistics()

    def detach(self):
        self.vbox1.reparent(self.window2)

    def do_cal_update(self, trans_attr, cal):
        setattr(self.trans, trans_attr, convert_gtk_cal_date(cal))
        self.update_statistics()

    def on_remit_start_cal_day_selected(self, cal, *args):
        if self.gui_lock: return
        self.do_cal_update('period_start', cal)

    def on_end_of_remitt_cal_day_selected(self, cal, *args):
        if self.gui_lock: return
        self.do_cal_update('period_end', cal)
    
    def on_remit_date_cal_day_selected(self, cal, *args):
        if self.gui_lock: return
        self.trans.remitt_date = convert_gtk_cal_date(cal)
        self.trans.set_period_start_and_end_from_remmit_date()
        self.set_period_calendars()
        self.update_statistics()

    def set_period_calendars(self):
        assert( not self.gui_lock )
        self.gui_lock = True
        if self.trans.period_start != None:
            set_gtk_cal_to_date(self.remit_start_cal, self.trans.period_start)
        if self.trans.period_end != None:
            set_gtk_cal_to_date(self.end_of_remitt_cal, self.trans.period_end)
        self.gui_lock = False

    def set_remit_date_calendar(self):
        assert( not self.gui_lock )
        self.gui_lock = True
        if self.trans.remitt_date != None:
            set_gtk_cal_to_date(self.remit_date_cal, self.trans.remitt_date)
        self.gui_lock = False
        
    def update_statistics(self):
        for label, val in (
            (self.num_employ_label, self.trans.num_employees()),
            (self.gross_pay_label, "$%s" % self.trans.get_gross_pay()),
            (self.num_periods_label, self.trans.num_paydays()),
            (self.remittance_label, "$%s" % self.trans.get_remitt()),
            ):
            label.set_text(str(val))
        
        


            
