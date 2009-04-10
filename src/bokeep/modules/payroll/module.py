from persistent import Persistent

class PayrollModule(Persistent):
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

    def set_employee_attr(self, employee_ident, attr_name, attr_val):

        if attr_name == 'rate':
            attr_val = float(attr_val)

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
        del self.payday_database[ (payday_date, payday_serial) ]
        self._p_changed = True

    def get_paydays(self):
        return self.payday_database
    
    def has_payday(self, payday_date, payday_serial):
        self.ensure_payday_database()
        return (payday_date, payday_serial) in self.payday_database

    def get_payday(self, payday_date, payday_serial):
        self.ensure_payday_database()
        return self.payday_database[(payday_date, payday_serial)]

