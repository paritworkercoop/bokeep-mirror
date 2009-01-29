#!/usr/bin/env python

# Python library
from sys import argv

# ZODB
import transaction

# Bo-Keep
from bokeep.config import get_database_cfg_file
from bokeep.book import BoKeepBookSet
from bokeep.modules.payroll.payroll import Payday, Employee, \
    PaystubCalculatedLine, PaystubNetPaySummaryLinePersist
from bokeep.util import ends_with_commit

PAYROLL_MODULE = 'bokeep.modules.payroll'

def print_paystubs(payday):
    from payroll_configuration import print_paystub_line_config
    for paystub in payday.paystubs:
        print paystub.employee.name
        for (line_name, function) in print_paystub_line_config:
            print line_name, '%.2f' % function(paystub)
        print ''

def add_new_payroll(book, payroll_module):
    from payday_data import paydate, payday_serial, emp_list
    from payroll_configuration import \
        paystub_line_config, paystub_accounting_line_config
    
    if payroll_module.has_payday(paydate, payday_serial):
        answer = raw_input("the payroll dated %s with serial %s has already "
                           "been run. Do you want to remove it and "
                           "reprocess? > " % (
                paydate, payday_serial))
        answer = answer.lower()
        if answer == "yes" or answer == "y":
            (payday_trans_id, payday) = payroll_module.get_payday(
                paydate, payday_serial)
            payroll_module.remove_payday(paydate, payday_serial)
            book.remove_transaction(payday_trans_id)
        else:
            return None
    
    payday = Payday(paydate)
    payday_trans_id = book.insert_transaction(payday)
    payroll_module.add_payday(paydate, payday_serial, payday_trans_id, payday)

    for emp in emp_list:
        employee_name = emp['name']
        if not payroll_module.has_employee(employee_name):
            employee = Employee(employee_name)
            payroll_module.add_employee(employee_name, employee)
        else:                                        
            employee = payroll_module.get_employee(employee_name)
        paystub = employee.create_and_add_new_paystub(payday)
        for key, value in emp.iteritems():
            function = paystub_line_config[key]
            function( employee, emp, paystub, value )
    
        assert( 0==len(list(
                    paystub.get_paystub_lines_of_class(
                        PaystubNetPaySummaryLinePersist))))
        paystub.add_paystub_line( PaystubNetPaySummaryLinePersist(paystub) )

    # freeze all calculated paystub lines with current values to avoid
    # unesessary recalculation
    for paystub in payday.paystubs:
        for paystub_line in paystub.get_paystub_lines_of_class(
            PaystubCalculatedLine):
            paystub_line.freeze_value()
    
    for i in xrange(2):
        print_paystubs(payday)
        
    def generate_each_paystub_accounting_line(paystub, account_line_config):
        for single_account_line_config in account_line_config:
            for paystub_line in single_account_line_config[2](paystub):
                yield (single_account_line_config[0],
                       single_account_line_config[1],
                       paystub_line )

    payday_accounting_lines = [ [[], []],
                                [{}, {}],
                                [[], []] ]

    for paystub in payday.paystubs:
        for i in xrange(2):
            payday_accounting_lines[0][i].extend(
                generate_each_paystub_accounting_line(
                    paystub,
                    paystub_accounting_line_config[0][i] )
                )
        
        for i in xrange(2):
            for line_spec in paystub_accounting_line_config[1][i]:
                line_spec_key = (line_spec[0], line_spec[1], line_spec[2])
                if line_spec_key not in payday_accounting_lines[1][i]:
                    payday_accounting_lines[1][i][line_spec_key] = []
                payday_accounting_lines[1][i][line_spec_key].extend(
                    paystub_line
                    for paystub_line in line_spec[3](paystub)
                    )

        #new_per_employee_trans = [[], []]
        #for i in xrange(2):
        #    new_per_employee_trans[i].extend( 
        #        generate_each_paystub_accounting_line(
        #            paystub,
        #            payday_accounting_lines[2][i] ) )

        #for i in xrange(2):
        #    if len(new_per_employee_trans[0]) > 0:
        #               if len(new_per_employee_trans[0][i]) > 0:
        #                   payday_accounting_lines[2][i].append(
         #                      new_per_employee_trans )
        

    payday.specify_accounting_lines(payday_accounting_lines)
    payday.print_accounting_lines()

    book.get_backend_module().mark_transaction_dirty(payday_trans_id)

@ends_with_commit
def payroll_main(bookset):
    book = bookset.get_book(argv[1])

    if not book.has_module(PAYROLL_MODULE):
        book.add_module(PAYROLL_MODULE)

    if book.has_module_disabled(PAYROLL_MODULE):
        book.enable_module(PAYROLL_MODULE)

    payroll_module = book.get_module(PAYROLL_MODULE)

    add_new_payroll(book, payroll_module)

def bokeep_main():
    bookset = BoKeepBookSet( get_database_cfg_file() )
    payroll_main(bookset)
    bookset.close_primary_connection()

if __name__ == "__main__":
    bokeep_main()

