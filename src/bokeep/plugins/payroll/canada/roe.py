# employee.py
# Copyright (C) 2011 ParIT Worker Co-operative <paritinfo@parit.ca>
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
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
# Author(s): Jamie Campbell <jamie@parit.ca>
#            Mark Jenkins <mark@parit.ca>

def write_ROE_to_buffer(
    payroll_plugin, employee, start_roe, end_roe, roe_file,
    employer_name_and_address,
    cra_number,
    pay_period_type="Biweekly",
    ignore_timesheet=False,
    force_each_pay_period=False,
    ):
    # http://www.servicecanada.gc.ca/eng/ei/employers/roe_guide.shtml ,
    # is the overall guide here to what is being achieved

    #verify that the specified work term period is an actual work term period
    if not employee.roe_work_period_exists(start_roe, end_roe):
        raise Exception(
            "The employee does not have a work period for the requested "
            "start and end dates.")

    employee_name = (employee.name if not hasattr(employee, "_name")
                     else employee._name )

    roe_file.write('Record of employment for ' + employee_name + '\n\n')
    roe_file.write("Block 4 (Employer's name and address): " + employer_name_and_address + "\n")
    roe_file.write("Block 5 (CRA Business Number (BN)): " + cra_number + "\n")
    roe_file.write("Block 6 (Pay period type): " + pay_period_type + "\n")

    first_day_worked = start_roe
    roe_file.write("Block 10 (First day worked): " + str(first_day_worked) + "\n")

    # period_paystubs = employee.get_paystubs_for_roe_work_period(start_roe, end_roe)  

    #note that there may be information included before start date and after end 
    #date, it is the PERIODS that contain these dates that serve as the bounding
    #points, not the dates themselves.
    paydays = payroll_plugin.get_paydays(start_roe, end_roe)

    sorted_paydays_list = []
    emp_specific_paydays = []
    for payday in sorted(paydays.itervalues()):
         sorted_paydays_list.append(payday)
         stubs = payday.paystubs
         if not(self.get_empstub(stubs, employee.name) == None):
             emp_specific_paydays.append(payday)

    if len(emp_specific_paydays) == 0:
        #Can't sensibly generate an ROE for an employee who never worked
        raise Exception("Can't generate a sensible ROE, the employee has no paystubs for the requested range.")
    else:
        last_payday = emp_specific_paydays[len(emp_specific_paydays)-1]
        last_date = payday.period_end
        final_pay_period_date = last_date


    if ignore_timesheet:
        # this is the best approximation we can make without timesheets
        last_day_worked = final_pay_period_date
    else:
        last_timesheet = employee.get_last_timesheet(end_roe)
        if last_timesheet == None:
            # this should actually never happen and the old code we have here
            # isn't good, you don't want to say there was no timesheet...
            # when we're expecting one
            raise Exception("Last timesheet not found")
            #last_day_worked = first_day_worked
        else:
            last_day_worked = last_timesheet.sheet_date
    
    roe_file.write("Block 11 (Last day for which paid): " + str(last_day_worked) + "\n")
    roe_file.write("Block 12 (Final pay period ending date): " + str(final_pay_period_date) + "\n")

    processed_payperiods = 0
    insurable_hours = 0.0

    reversed_paydays = list(reversed(sorted_paydays_list))

    # other pay period types not supported right now
    assert( pay_period_type == "Biweekly" )
    for payday in reversed_paydays:
        stubs = payday.paystubs
        empstub = self.get_empstub(stubs, employee.name)
        if not (empstub == None):
           #get hours for this period
           pd = payday
           assert(not ignore_timesheet)
           applicable_timesheets = None
           if hasattr(pd, 'period_start') and hasattr(pd, 'period_end'):
               applicable_timesheets = employee.get_timesheets(pd.period_start, pd.period_end)
           else:
               applicable_timesheets = employee.get_timesheets(pd.paydate, pd.paydate)
           for timesheet in applicable_timesheets:
               insurable_hours += timesheet.hours

        if not (empstub == None) or processed_payperiods > 0:
           processed_payperiods += 1

        if processed_payperiods == 27:
            break

    total_insurable_hours = insurable_hours
    earnings_by_period_list = []
    processed_payperiods = 0
    insurable_payperiods = 0
    insurable_earnings = Decimal('0.0')
    earnings_by_period_str = ''

    assert(False)
    for payday in reversed_paydays:
        stubs = payday.paystubs
        empstub = self.get_empstub(stubs, employee.name)
        if not (empstub == None):
            curr_earnings = Decimal('0.0')
            for line in empstub.paystub_lines:
                if line.description == 'wages':
                    insurable_earnings += line.get_value()
                    curr_earnings += line.get_value()
            insurable_payperiods += 1
            period_number = processed_payperiods+1
            period_earnings = float(str(curr_earnings))
            earnings_by_period_list.append(
                (period_number, period_earnings))
        elif processed_payperiods > 0:
            period_number = processed_payperiods+1
            period_earnings = 0.0
            earnings_by_period_list.append(
                (period_number, period_earnings) )

        if not (empstub == None) or processed_payperiods > 0:
            processed_payperiods += 1

        if processed_payperiods == 14:
            break

    total_insurable_earnings = float(str(insurable_earnings))

    roe_file.write("Block 15A (Total insurable hours): " + str(total_insurable_hours) + "\n") 
    roe_file.write("Block 15B (Total insurable earnings): " + str(total_insurable_earnings) + "\n")

    #section 15c is ONLY to be filled out if there are any gaps
    if insurable_payperiods < processed_payperiods or force_each_pay_period:
        roe_file.write("Block 15c (insurable earnings per period): \n")
        for period_number, period_earnings in total_insurable_earnings_by_period:
            roe_file.write(str(period_number) + ': $' + str(period_earnings) + '\n')


if __name__ == "__main__":
    import bokeep.plugins.payroll
    from bokeep.plugins.payroll.payroll import Payday
    from bokeep.plugins.payroll.canada.employee import Employee
    from bokeep.plugins.payroll.canada.paystub import Paystub
    from sys import stdout
    from datetime import date, timedelta
    payroll_plugin =  bokeep.plugins.payroll.get_plugin_class()()
    employee_name = 'test employee'
    employee = Employee(employee_name)
    payroll_plugin.add_employee(employee_name, employee)
    DAY_ZERO = date(2011, 1, 6)
    PAYDAY = DAY_ZERO + timedelta(days=14)
    employee.add_timesheet( DAY_ZERO, 3.4, 'wtf' )
    payday_obj = Payday(payroll_plugin)
    payday_obj.set_paydate( DAY_ZERO, PAYDAY, PAYDAY )
    paystub = Paystub(employee, payday_obj)
    
    employee.start_roe_work_period(DAY_ZERO)
    employee.end_roe_work_period(PAYDAY)

    write_ROE_to_buffer(
        payroll_plugin, employee,
        DAY_ZERO,
        PAYDAY, stdout,
        "employer X lives at home",
        "XXXXX",        
        )
