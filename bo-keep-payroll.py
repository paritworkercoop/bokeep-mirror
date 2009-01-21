#!/usr/bin/env python

# Python library
from sys import argv

# ZODB
import transaction

# Bo-Keep
from bokeep.config import get_database_cfg_file
from bokeep.book import BoKeepBookSet
from bokeep.modules.payroll.payroll import Payday, Employee

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
        employee = payroll_module.get_employee( emp['name'] )
        paystub = employee.create_and_add_new_paystub(payday)
        for key, function in paystub_line_config:
            if key in emp:
                function( employee, emp, paystub, emp[key] )
    
    for i in xrange(2):
        print_paystubs(payday)

    payday.specify_account_mapping(paystub_accounting_line_config)

    book.get_backend_module().mark_transaction_dirty(payday_trans_id)

def bokeep_main():
    bookset = BoKeepBookSet( get_database_cfg_file() )
    book = bookset.get_book(argv[1])
    payroll_module = book.get_module('bokeep.modules.payroll')

    if len(argv) >= 3:
        if argv[2] == "add" and argv[3] == "employee":
            payroll_module.add_employee( argv[4], Employee(argv[4]))
        elif argv[2] == "print" and argv[3] == "employee":
            print str(payroll_module.get_employee( argv[4] ))
    else:
        add_new_payroll(book, payroll_module)

    transaction.get().commit()
    bookset.close_primary_connection()

if __name__ == "__main__":
    bokeep_main()

