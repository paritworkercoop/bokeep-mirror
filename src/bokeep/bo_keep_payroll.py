#!/usr/bin/python

# Python library
from sys import argv
import sys

import os
from os import P_NOWAIT

# Hello, I'm ZODB
import transaction

# Bo-Keep, keeper of the Bo
from bokeep.config import get_database_cfg_file
from bokeep.book import BoKeepBookSet
from bokeep.modules.payroll.payroll import Payday, Employee, \
    PaystubCalculatedLine, PaystubNetPaySummaryLine
from bokeep.util import ends_with_commit

from datetime import date, datetime
PAYROLL_MODULE = 'bokeep.modules.payroll'

def print_paystub(paystub):
    from payroll_configuration import print_paystub_line_config
    paystub_file = open('PaystubPrint.txt', 'a')
    paystub_file.write(paystub.employee.name + '\n')
    for (line_name, function) in print_paystub_line_config:
	outstr = line_name + ': ' + str('%.2f' % function(paystub))
        paystub_file.write(outstr + '\n')
    paystub_file.write(chr(0x0c) + '\n')

def print_paystubs(payday):
    #nuke paystub data from any prior runs
    newfile = open('PaystubPrint.txt', 'w')
    newfile.close()
    for paystub in payday.paystubs:
        print_paystub(paystub)

def add_new_payroll(book, payroll_module, display_paystubs, ask_user_reprocess=True):
    from payday_data import paydate, payday_serial, emp_list, chequenum_start, period_start, period_end
    from payroll_configuration import \
        paystub_line_config, paystub_accounting_line_config
    
    # if a payroll has already been run with the same date and serial number
    # ask to remove it
    if payroll_module.has_payday(paydate, payday_serial):
        answer = 'yes'
        if ask_user_reprocess:
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
    
    payday = Payday(paydate, period_start, period_end)
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
        for key, function in paystub_line_config:
            if key in emp:
                function( employee, emp, paystub, emp[key] )
    
        assert( 0==len(list(
                    paystub.get_paystub_lines_of_class(
                        PaystubNetPaySummaryLine))))
        paystub.add_paystub_line( PaystubNetPaySummaryLine(paystub) )

    # freeze all calculated paystub lines with current values to avoid
    # unesessary recalculation
    for paystub in payday.paystubs:
        for paystub_line in paystub.get_paystub_lines_of_class(
            PaystubCalculatedLine):
            paystub_line.freeze_value()
    
    print_paystubs(payday)
       
    #possibility of supporting stuff other than 'name' in futue
    def parse_accounting_line_variables(paystub, scoping):
       
        listver = []
 
        for i in range(0, len(scoping)):
            if scoping[i].startswith('$name'):
                listver.append(paystub.employee.name)
            else:
                listver.append(scoping[i])
            
        return tuple(listver)

    def generate_each_paystub_accounting_line(paystub, account_line_config):
        """Given a paystub and list of accounting specifications
        (each of which is a three element tuple, consiting of an
         account in accounting an program,
         a line description for accounting program,
         and a function that generates sub subset of paystub lines in
         the paystub),
         this function yields a tuple for containing each PaystubLine
         with account and line description that the configuration specifies
        """
        for single_account_line_config in account_line_config:
            for paystub_line in single_account_line_config[2](paystub):
                yield (parse_accounting_line_variables(paystub, single_account_line_config[0]),
                      single_account_line_config[1],
                       paystub_line )

    payday_accounting_lines = [
        # per employee lines, main payroll transaction
        # debits (0) and credits (1)
        [[], []],

        # lines to be accumulated together across
        # multiple employee paystubs
        # debits (0) and credits (1)
        [{}, {}],

        chequenum_start
        ]

    # for each paystub, build up financial accounting transactions for
    # all its paystub lines according to the specification in
    # paystub_accounting_line_config[0][i]
    for paystub in payday.paystubs:
        # generate the per employee lines that will appear in the main payroll
        # transaction
        #
        # do both the debits (0) and the credits (1)
        for i in xrange(2):
            payday_accounting_lines[0][i].extend(
                generate_each_paystub_accounting_line(
                    paystub,
                    paystub_accounting_line_config[0][i] )
                )
        
        
        # generate the lines that are to be accumulated together across
        # multiple employee paystubs
        #
        # debits (0) and credits (1)
        for i in xrange(2):
            for line_spec in paystub_accounting_line_config[1][i]:
                line_spec_key = (line_spec[0], line_spec[1], line_spec[2])
                if line_spec_key not in payday_accounting_lines[1][i]:
                    payday_accounting_lines[1][i][line_spec_key] = []
                payday_accounting_lines[1][i][line_spec_key].extend(
                    paystub_line
                    for paystub_line in line_spec[3](paystub)
                    )

        # generate any per employee transactions
        new_per_employee_trans = [[], []]
        # do both the debits (0) and the credits (1)
        for i in xrange(2):
            new_per_employee_trans[i].extend( 
                generate_each_paystub_accounting_line(
                    paystub,
                    paystub_accounting_line_config[2][i] ) )
        new_per_employee_trans.append( paystub.employee.name )

        if len(new_per_employee_trans[0]) > 0:
            if len(new_per_employee_trans[0][0]) > 0:
                payday_accounting_lines.append(
                    new_per_employee_trans )
        
    
    payday.specify_accounting_lines(payday_accounting_lines)
    backend_module = book.get_backend_module()
    backend_module.mark_transaction_dirty(payday_trans_id,
                                          payday)
    backend_module.flush_backend()

    if (display_paystubs):
        print 'spawning oowriter'
        os.spawnv(P_NOWAIT, '/usr/bin/oowriter', ['0', 'PaystubPrint.txt'])
    

def payroll_init(bookname, bookset=None):
    if (bookset == None):
        bookset = BoKeepBookSet( get_database_cfg_file() )

    book = bookset.get_book(bookname)

    payroll_module = payroll_get_payroll_module(bookname, bookset)

    return bookset, book, payroll_module

def payroll_add_employee(bookname, emp_name, bookset=None):
    bookset, book, payroll_module = payroll_init(bookname, bookset)
    if not payroll_module.has_employee(emp_name):
        employee = Employee(emp_name)
        payroll_module.add_employee(emp_name, employee)
        transaction.get().commit()
    bookset.close()

def payroll_get_employees(bookname, bookset=None):
    bookset, book, payroll_module = payroll_init(bookname, bookset)
    return [payroll_module.get_employees(), bookset]

def payroll_get_employee(bookname, bookset, emp_name):    
    bookset, book, payroll_module = payroll_init(bookname, bookset)
    if payroll_module.has_employee(emp_name):
        return payroll_module.get_employee(emp_name)
    else:
        return None

def payroll_get_paydays(bookname, bookset=None):
    bookset, book, payroll_module = payroll_init(bookname, bookset)
    return payroll_module.get_paydays()

def payroll_get_payday(bookname, date, serial, bookset=None):
    bookset, book, payroll_module = payroll_init(bookname, bookset)
    if payroll_module.has_payday(date, serial):
        return payroll_module.get_payday(date, serial)
    else:
        return None

@ends_with_commit
def payroll_remove_payday(bookname, date, serial, bookset=None):
    bookset, book, payroll_module = payroll_init(bookname, bookset)
    if payroll_module.has_payday(date, serial):
        payroll_module.remove_payday(date, serial)
        return True
    else:
        return False
    
def payroll_runtime(bookname, ask_user_reprocess=True, display_paystubs=False, bookset=None):
    bookset, book, payroll_module = payroll_init(bookname, bookset)

    add_new_payroll(book, payroll_module, display_paystubs, ask_user_reprocess)

    bookset.close()

def payroll_has_payday_serial(bookname, paydate, payday_serial):
    bookset, book, payroll_module = payroll_init(bookname)

    return payroll_module.has_payday(paydate, payday_serial)
    
    bookset.close()
    

@ends_with_commit
def payroll_run_main(bookset):
    payroll_runtime(argv[1], True, False, bookset)


@ends_with_commit
def payroll_set_employee_attr(bookname, bookset, empname, attr_name, attr_val):
    bookset, book, payroll_module = payroll_init(bookname, bookset)
    payroll_module.set_employee_attr(empname, attr_name, attr_val)

def payroll_set_all_employee_attr(bookname, bookset, attr_name, attr_val):
    bookset, book, payroll_module = payroll_init(bookname, bookset)
    payroll_module.set_all_employee_attr(attr_name, attr_val)

def payroll_add_timesheet(bookname, emp_name, sheet_date, hours, memo, bookset=None):
    bookset, book, payroll_module = payroll_init(bookname, bookset)
    if payroll_module.has_employee(emp_name):
        payroll_module.add_timesheet(emp_name, sheet_date, hours, memo)
        transaction.get().commit()
        bookset.close()
        return True
    else:
        bookset.close()
        return False

def payroll_get_payroll_module(bookname, bookset):
    book = bookset.get_book(bookname)

    if not book.has_module(PAYROLL_MODULE):
        book.add_module(PAYROLL_MODULE)

    if book.has_module_disabled(PAYROLL_MODULE):
        book.enable_module(PAYROLL_MODULE)

    payroll_module = book.get_module(PAYROLL_MODULE)
    return payroll_module


def payroll_employee_command(bookname, bookset, command_type, args):
    bookset, book, payroll_module = payroll_init(bookname, bookset)
    if command_type == 'add':
        if args[0] == 'timesheet':
            try:
                dt = datetime.strptime(args[2], "%B %d, %Y")
                d = date(dt.year, dt.month, dt.day)
                payroll_add_timesheet(bookname, args[1], d, float(args[3]), args[4], bookset)
            except ValueError:
                print "I didn't understand your date format.  Please use Month Day, Year (for example 'March 29, 2009'  The spaces are important, I'm a fragile creature who can't understand 'March 29,2009')"

        else:
            payroll_add_employee(bookname, args[0], bookset)
    elif command_type == 'get':
        if args[0] == 'all':
            emps, bookset = payroll_get_employees(bookname, bookset)
            print 'current employees:\n'
            for employee_name in emps:
                print str(emps[employee_name]) + '\n'
        else:
            emp = payroll_get_employee(bookname, bookset, args[0])
            print str(emp)
    elif command_type == 'set':
        if args[0] == 'all':
            payroll_set_all_employee_attr(bookname, bookset, args[1], args[2])
        else:
            payroll_set_employee_attr(bookname, bookset, args[0], args[1], args[2])

    bookset.close()
        

def payroll_payday_command(bookname, bookset, command_type, args):
    bookset, book, payroll_module = payroll_init(bookname, bookset)
    if command_type == 'run':
        payroll_run_main(bookset)
    elif command_type == 'get':
        if args[0] == 'all':
            paydays = payroll_get_paydays(bookname, bookset)
            print 'paydays in database:\n'
            for payday in paydays:
                print str(payday)
        else:
            try:
#                print 'you are trying to get payday for ' + str(datetime.strptime(args[0], "%B %d, %Y"))
                dt = datetime.strptime(args[0], "%B %d, %Y")
                d = date(dt.year, dt.month, dt.day)
                payday = payroll_get_payday(bookname, d, int(args[1]), bookset)    
            except ValueError:
                print "I didn't understand your date format.  Please use Month Day, Year (for example 'March 29, 2009'  The spaces are important, I'm a fragile creature who can't understand 'March 29,2009')"

            if payday == None:
                print "sorry, I couldn't find that payday"
            else:
                print str(payday[1])
    elif command_type == 'drop':
        try:
            #we can add 'drop all' if we want, but that seems kind of dangerous and
            #like something way too easy to do accidentally
            dt = datetime.strptime(args[0], "%B %d, %Y")
            d = date(dt.year, dt.month, dt.day)
            removed = payroll_remove_payday(bookname, d, int(args[1]), bookset)
        except ValueError:
            print "I didn't understand your date format.  Please use Month Day, Year (for example 'March 29, 2009'  The spaces are important, I'm a fragile creature who can't understand 'March 29,2009')"

        if removed == True:
            print 'payday(' + str(dt) + ',' + args[1] + ') dropped.'
        else:
            print "sorry, I couldn't find that payday"
      
    bookset.close()

def bokeep_main():
    bookset = BoKeepBookSet( get_database_cfg_file() )
    if argv[2] == 'payday':
        payroll_payday_command(argv[1], bookset, argv[3], argv[4:])
    elif argv[2] == 'emp':
        payroll_employee_command(argv[1], bookset, argv[3], argv[4:])
    else:
        print 'unrecognized command ' + argv[2]


if __name__ == "__main__":
    bokeep_main()

