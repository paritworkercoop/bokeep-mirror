# Copyright (C) 2010-2011  ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
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

# bokeep imports
from bokeep.prototype_plugin import PrototypePlugin
from bokeep.plugins.payroll.payroll import Payday

CDN_PAYROLL_CODE = 0

class PayrollPlugin(PrototypePlugin):
    # configuration_file is a new attribute added during 1.0.3 development
    def __init__(self):
        self.employee_database = {}
        self.payday_database = {}
        self.set_config_file(self.get_config_file())

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

    def register_transaction(self, trans_id, payday_trans):
        assert( not self.has_transaction(trans_id) )
        self.payday_database[trans_id] = payday_trans
        self._p_changed = True

    def purge_all_paystubs(self, payday_to_remove):
        # remove paystubs from this payday if associated with an employee
        #
        # perhaps a good argument for being rid of employees referencing
        # thier own paystubs seeing how this was once absent...
        for name, employee in self.get_employees().iteritems():
            new_paystubs = [
                paystub
                for paystub in employee.paystubs
                if paystub not in payday_to_remove.paystubs
                ]
            employee.paystubs = new_paystubs        

        # implicit set of payday_to_remove._p_changed = True
        payday_to_remove.paystubs = []

    def remove_transaction(self, trans_id):
        assert( self.has_transaction(trans_id) )
        payday_to_remove = self.payday_database[trans_id]
        del self.payday_database[trans_id]
        self._p_changed = True
        self.purge_all_paystubs(payday_to_remove)

    def has_transaction(self, trans_id):
        return trans_id in self.payday_database

    #note that there may be information included before start date and after end 
    #date, it is the PERIODS that contain these dates that serve as the bounding
    #points, not the dates themselves.
    def get_paydays(self, start_date=None, end_date=None):
        if start_date == None or end_date == None:
            return self.payday_database
        else:
            #return bounded info
            bounded_entries = {}
            # kind of shocked this isn't returned sorted...
            for trans_id, payday in self.payday_database.iteritems():
                if end_date < payday.period_start or \
                        start_date > payday.period_end:
                    continue
                else:
                    assert( not trans_id in bounded_entries )
                    bounded_entries[trans_id] = payday
            return bounded_entries
    
    def gen_paydays_with_paydate_bounds(self, start_date, end_date):
        # too bad this can't take advantage of some kind of sort or
        # index to run faster
        return (
            payday
            for payday in self.payday_database.itervalues()
            if start_date <= payday.paydate
            if end_date >= payday.paydate )

    def has_payday(self, payday_date):
        """Search for a (only 1!) payday with a particular date

        You're much better off caling get_payday if you're indending to do
        a check and a fetch, cause you can just check the return value of that
        """
        trans_id, payday = self.get_payday(payday_date)
        return payday != None

    def get_payday(self, payday_date):
        """Fetch a payday by paydate

        Return None if no payday with that payday is found
        """
        # linear search.., if this grows to big we'll need a index of paydays
        # by date...
        for trans_id, payday in self.payday_database.iteritems():
            if payday.paydate == payday_date:
                return trans_id, payday
        return None, None

    def get_config_file(self):
        return getattr(self, 'configuration_file', None)
    
    def set_config_file(self, config_file):
        self.configuration_file = config_file

    def run_configuration_interface(
        self, parent_window, backend_account_fetch):
        # imported here to avoid importing graphics code at top
        # makes tests without a display avoid calling gtk and
        # no graphics error
        from gui.config import PayrollConfigDialog
        dia = PayrollConfigDialog(parent_window, backend_account_fetch,
                                  self)
        dia.run()
        
    @staticmethod
    def get_transaction_type_codes():
        return (CDN_PAYROLL_CODE,)

    @staticmethod
    def get_transaction_type_from_code(code):
        assert( code == CDN_PAYROLL_CODE )
        return Payday

    @staticmethod
    def get_transaction_type_pulldown_string_from_code(code):
        assert( code == CDN_PAYROLL_CODE )
        return "Manitoba/Canadian payroll"

    @staticmethod
    def get_transaction_edit_interface_hook_from_code(code):
        # imported here to avoid an import of gui code (with dependency
        # on gtk at the top). This makes running the tests
        # without a gtk compatible display possible without a warning msg
        from gui.plain_text_selector import CanadianPayrollEditor
        assert( code == CDN_PAYROLL_CODE )
        return CanadianPayrollEditor


            
