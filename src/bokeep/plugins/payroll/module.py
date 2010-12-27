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
from persistent import Persistent
from bokeep.prototype_plugin import PrototypePlugin

class PayrollModule(PrototypePlugin):
    def __init__(self):
        self.employee_database = {}
        self.init_payday_database()
    
    def init_payday_database(self):
        self.payday_database = {}

    def ensure_payday_database(self):
        if not hasattr(self, 'payday_database'):
            self.init_payday_database()

    def add_employee(self, employee_ident, employee):
        self.employee_database[employee_ident] = employee
        self._p_changed = True

    def add_timesheet(self, employee_ident, sheet_date, hours, memo):
        employee = self.employee_database[employee_ident]
        employee.add_timesheet(sheet_date, hours, memo)
        self._p_changed = True

    def drop_timesheets(self, employee_ident, start_drop, end_drop):
        employee = self.employee_database[employee_ident]
        employee.drop_timesheets(start_drop, end_drop)
        self._p_changed = True

    def get_timesheets(self, employee_ident, start_get, end_get):
        employee = self.employee_database[employee_ident]
        return employee.get_timesheets(start_get, end_get)

    def set_employee_attr(self, employee_ident, attr_name, attr_val):

        if attr_name == 'rate':
            attr_val = float(attr_val)

        #if the name is being changed then we need to reindex the employee
        if attr_name == 'name':
            self.employee_database[attr_val] = self.employee_database[employee_ident]
            setattr(self.employee_database[attr_val], attr_name, attr_val)
            self.employee_database[attr_val]._p_changed = True

            #remove the old key.
            del self.employee_database[employee_ident]
            self._p_changed = True


        if self.has_employee(employee_ident):
            emp = self.get_employee(employee_ident)
            setattr(emp, attr_name, attr_val)
            self._p_changed = True

    def set_all_employee_attr(self, attr_name, attr_val):
        for emp in self.employee_database:
            self.set_employee_attr(emp, attr_name, attr_val)

    def has_employee(self, employee_ident):
        return employee_ident in self.employee_database
        
    def get_employee(self, employee_ident):
        return self.employee_database[employee_ident]

    def get_employees(self):
        return self.employee_database

    def add_payday(self, payday_date, payday_serial, payday_trans_id, payday):
        self.ensure_payday_database()
        assert( (payday_date, payday_serial) not in self.payday_database )
        self.payday_database[ (payday_date, payday_serial) ] = \
            (payday_trans_id, payday)
        self._p_changed = True

    def remove_payday(self, payday_date, payday_serial):
        key = (payday_date, payday_serial) 
        id, payday_to_remove = \
        self.payday_database[key]
        del self.payday_database[key]
        # remove paystubs from this payday if associated with an employee
        # this was originally missed, which was a pretty severre bug
        # as paystubs would be left in the employee while removed
        # from the payday
        #
        # that this was missed illustrates that it having both employee and
        # payday reference paystubs was a bad idea.
        #
        # referencing the same thing in many places means one hand can
        # forget what the other was doing...
        for name, employee in self.get_employees().iteritems():
            new_paystubs = [
                paystub
                for paystub in employee.paystubs
                if paystub not in payday_to_remove.paystubs
                ]
            employee.paystubs = new_paystubs
        self._p_changed = True

    #note that there may be information included before start date and after end 
    #date, it is the PERIODS that contain these dates that serve as the bounding
    #points, not the dates themselves.
    def get_paydays(self, start_date=None, end_date=None):
        if start_date == None or end_date == None:
            return self.payday_database
        else:
            #return bounded info
            bounded_entries = {}
            for entry in self.payday_database:
                pstart = self.payday_database[entry][1].period_start
                pend = self.payday_database[entry][1].period_end
                if end_date < pstart or start_date > pend:
                    continue
                else:                
                    bounded_entries[entry] = self.payday_database[entry]
            return bounded_entries
    
    def has_payday(self, payday_date, payday_serial):
        self.ensure_payday_database()
        return (payday_date, payday_serial) in self.payday_database

    def get_payday(self, payday_date, payday_serial):
        self.ensure_payday_database()
        return self.payday_database[(payday_date, payday_serial)]

