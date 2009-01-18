from persistent import Persistent

class PayrollModule(Persistent):
    def __init__(self):
        self.employee_database = {}
    
    def add_employee(self, employee_ident, employee):
        self.employee_database[employee_ident] = employee
        self._p_changed = True
