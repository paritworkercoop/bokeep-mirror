# Python library
from sys import argv
import sys

import os
from os import P_NOWAIT

# Hello, I'm ZODB
import transaction

# cndpayroll imports
from cdnpayroll.paystub_line import sum_paystub_lines
from cdnpayroll.vacation_pay import VacationPayoutTooMuchException

# Bo-Keep (keeper of the Bo) imports
from bokeep.modules.payroll.payroll import PaystubWageLine

from bokeep.config import get_database_cfg_file
from bokeep.book import BoKeepBookSet
from bokeep.modules.payroll.payroll import Payday, Employee, \
    PaystubCalculatedLine, PaystubNetPaySummaryLine
from bokeep.util import ends_with_commit


from datetime import date, datetime

from decimal import Decimal

PAYROLL_MODULE = 'bokeep.modules.payroll'

RUN_PAYROLL_SUCCEEDED = 0
PAYROLL_ALREADY_EXISTS = 1 
PAYROLL_ACCOUNTING_LINES_IMBALANCE = 2
PAYROLL_MISSING_NET_PAY = 3
PAYROLL_TOO_MANY_DEDUCTIONS = 4
PAYROLL_DATABASE_MISSING_EMPLOYEE = 5
PAYROLL_VACPAY_DRAW_TOO_MUCH = 6

def decimal_from_float(float_value, places=2):
    formatstring = '%.' + str(places) + 'f'
    return_value = Decimal(formatstring % float_value)
    return return_value

def decimal_from_whatever(value, places=2):
    if type(value) == float:
        return decimal_from_float(value, places)
    elif type(value) == Decimal:
        return value.quantize( Decimal(10) ** (-places) )
    else: # covers int, string, and anything else Decimal() can handle..
        return Decimal(value).quantize( Decimal(10) ** (-places) )
    
def create_paystub_line(paystub_line_class):
    def return_function(employee, employee_info_dict, paystub, value):
        if value !=None:
            value = decimal_from_whatever(value)
        paystub.add_paystub_line( paystub_line_class(paystub, value) )
    return return_function


def create_paystub_wage_line(employee, employee_info_dict, paystub, value):
    rate = employee.default_rate

    if employee_info_dict.has_key('rate'):
        #normal employee rate (or default rate) is being overridden
        rate = employee_info_dict['rate']
    elif hasattr(employee, 'rate'):
        rate = employee.rate

    #    print 'period start is ' + str(paystub.payday.period_start) + ', period end is ' + str(paystub.payday.period_end)
#skip matching timesheets for the moment, need to put more thought into it
#    matching_timesheets = employee.get_timesheets(paystub.payday.period_start, paystub.payday.period_end)
    overall_hours = 0
    #    for timesheet in matching_timesheets:
    #        overall_hours += timesheet.hours

    #add any 'additional hours not on a timesheet'
    if employee_info_dict.has_key('hours'):
        overall_hours += employee_info_dict['hours']

    # convert and restrict the hours and rate to four decimals places to
    # retain some precision the result of multiplying them will become
    # two places elsewhere
    overall_hours = decimal_from_whatever(overall_hours, 4)
    rate = decimal_from_whatever(rate, 4)

    paystub.add_paystub_line(PaystubWageLine(paystub,
                                             overall_hours,
                                             rate ) )

def calc_line_override(override_cls):
    def return_function(employee, employee_info_dict, paystub, value):
        first = True
        for paystub_line in paystub.get_paystub_lines_of_class(override_cls):
            # set value of the first paystub line of override_cls to the user
            # specified value, set all other paystub lines of that type to 0
            if first:
                paystub_line.set_value(decimal_from_whatever(value))
            else:
                paystub_line.set_value(Decimal('0.00'))
            first = False
        
    return return_function

def negate_return_value(dec_func):
    """Input: A function that returns a GncNumeric value
    Output: A function that is like dec_func, but with the
    return value negated
    """
    def negate_dec_func(*args, **kargs):
        return - dec_func(*args, **kargs)
    return negate_dec_func

def negate_decorator_decorator(decorator_function):
    """Input: A decorator, a function that takes in a function and returns a
    function, where the returned function is based on the input function

    Output: A decorated version of the input function, decorated so that
    after it is called, the function it returns is decorated to have
    negated return values

    Yes, you read it correctly, this decorates a decorator.
    """
    def decorator_call(dec_func):
        return negate_return_value( decorator_function( dec_func ) )
    return decorator_call

def amount_from_paystub_line_of_class( paystub_line_class ):
    def retrieval_function(paystub):
        return sum_paystub_lines(
            paystub.get_paystub_lines_of_class( paystub_line_class ))
    return retrieval_function

@negate_decorator_decorator
def amount_from_paystub_line_of_class_reversed( paystub_line_class ):
    return amount_from_paystub_line_of_class(paystub_line_class)

def amount_from_paystub_function( paystub_function ):
    def retrieval_function(paystub):
        return paystub_function( paystub)
    return retrieval_function

@negate_decorator_decorator
def amount_from_paystub_function_reversed(paystub_function):
    return amount_from_paystub_function(paystub_function)

def calculated_value_of_class(class_name):
    def return_func(paystub):
        return sum ( line.get_calculated_value()
                     for line in paystub.get_paystub_lines_of_class(
                class_name) )
    return return_func

def value_of_class(class_name):
    def return_func(paystub):
        return sum( line.get_value()
                    for line in paystub.get_paystub_lines_of_class(class_name))
    return return_func

def value_component_at_index(class_name, index):
    def return_func(paystub):
        return sum ( line.get_value_components()[index]
                     for line in paystub.get_paystub_lines_of_class(
                class_name) )
    return return_func

def do_nothing(*args):
    pass

def lines_of_class_function(class_find):
    def new_func(paystub):
        return paystub.get_paystub_lines_of_class(class_find)
    return new_func


def lines_of_classes_and_not_classes_function(good_classes, bad_classes):
    def new_func(paystub):
        return paystub.get_paystub_lines_of_classes_not_classes(
            good_classes, bad_classes)
    return new_func

def create_and_tag_paystub_line(paystub_line_class, tag):
    def return_function(employee, employee_info_dict, paystub, value):
        value = decimal_from_whatever(value)
        new_paystub_line = paystub_line_class(paystub, value)
        setattr(new_paystub_line, tag, None)
        paystub.add_paystub_line(new_paystub_line)
    return return_function

def paystub_get_lines_of_class_with_tag(
    paystub, paystub_line_class, tag):
    return ( line
             for line in paystub.get_paystub_lines_of_class(
                 paystub_line_class)
             if hasattr(line, tag) )

def get_lines_of_class_with_tag(paystub_line_class, tag):
    def return_function(paystub):
        return paystub_get_lines_of_class_with_tag(
            paystub, paystub_line_class, tag)
    return return_function

def sum_line_of_class_with_tag(paystub_line_class, tag):
    def return_function(paystub):
        return sum( line.get_value()
                    for line in paystub_get_lines_of_class_with_tag(
                            paystub, paystub_line_class, tag)
                    )
    return return_function

def get_ytd_sum_of_class(paystub_line_class):
    def return_function(paystub):
        return paystub.employee.get_YTD_sum_of_paystub_line_class(
                        paystub_line_class, paystub, True)
    return return_function

def get_all_time_sum_of_class(paystub_line_class):
    def return_function(paystub):
        return paystub.employee.get_sum_of_all_paystub_line_class(
            paystub_line_class, paystub, True)
    return return_function


def payroll_succeeded(code):
    return code == RUN_PAYROLL_SUCCEEDED

def payroll_already_exists(code):
    return code == PAYROLL_ALREADY_EXISTS

def payroll_accounting_lines_imbalance(code):
    return code == PAYROLL_ACCOUNTING_LINES_IMBALANCE

def print_paystub(paystub, print_paystub_line_config, paystub_file):
    paystub_file.write(paystub.employee.name + '\n')
    for (line_name, function) in print_paystub_line_config:
	outstr = line_name + ': ' + str( function(paystub) )
        paystub_file.write(outstr + '\n')
    paystub_file.write('\f\n')

def print_paystubs(payday, print_paystub_line_config, filepath):
    #nuke paystub data from any prior runs
    prepender = ''
    if not (filepath == ''):
        prepender = filepath + '/'
    newfile = open(prepender + 'PaystubPrint.txt', 'w')
    for paystub in payday.paystubs:
        print_paystub(paystub, print_paystub_line_config, newfile)
    newfile.close()

def payday_accounting_lines_balance(transactions):
    # this should be removed, there shouldn't be an imbalance at all

    for trans in transactions.get_financial_transactions():
        #after all lines are processed, balance amount must be back to zero 
        #again otherwise we're imbalanced
        balance_amount = Decimal(0)
        for line in trans.lines:
            balance_amount += line.amount
 
        if not (abs(balance_amount) < Decimal('0.05')):
            print 'imbalance amount of ' + str(balance_amount)
            return False

    return True

def add_new_payroll_from_import(
    book, payroll_module, display_paystubs,
    overwrite_existing=False, add_missing_employees=False):
    from payday_data import paydate, payday_serial, emp_list, \
        chequenum_start, period_start, period_end
    from payroll_configuration import \
        paystub_line_config, paystub_accounting_line_config, \
        print_paystub_line_config

    assert( (0,None) == add_new_payroll(book, payroll_module, display_paystubs, paydate,
                    payday_serial, emp_list, chequenum_start,
                    period_start, period_end, paystub_line_config,
                    paystub_accounting_line_config,
                    print_paystub_line_config, '', overwrite_existing) )

def add_new_payroll(book, payroll_module, display_paystubs, paydate,
                    payday_serial, emp_list, chequenum_start, period_start,
                    period_end, paystub_line_config,
                    paystub_accounting_line_config,
                    print_paystub_line_config, file_path,
                    overwrite_existing=False, add_missing_employees=False):
    
    # if a payroll has already been run with the same date and serial number
    # ask to remove it
    if payroll_module.has_payday(paydate, payday_serial):
        if not (overwrite_existing):
            return PAYROLL_ALREADY_EXISTS, None
        else:
            # jeez, shouldn't there be a prompt here before we just go
            # on and remove? Didn't there use to be?
            (payday_trans_id, payday) = payroll_module.get_payday(
                paydate, payday_serial)
            payroll_module.remove_payday(paydate, payday_serial)
            book.remove_transaction(payday_trans_id)

    payday = Payday(paydate, period_start, period_end)
    payday_trans_id = book.insert_transaction(payday)
    payroll_module.add_payday(paydate, payday_serial,
                              payday_trans_id, payday)

    for emp in emp_list:
        employee_name = emp['name']
        if not payroll_module.has_employee(employee_name):
            if not add_missing_employees:
                payroll_module.remove_payday(paydate, payday_serial)
                book.remove_transaction(payday_trans_id)
                return PAYROLL_DATABASE_MISSING_EMPLOYEE, employee_name

            employee = Employee(employee_name)
            payroll_module.add_employee(employee_name, employee)
        else:                                        
            employee = payroll_module.get_employee(employee_name)
        paystub = employee.create_and_add_new_paystub(payday)
        paystub.add_paystub_line( PaystubNetPaySummaryLine(paystub))

        try:
            for key, function in paystub_line_config:
                if key in emp:
                    function( employee, emp, paystub, emp[key] )
        except VacationPayoutTooMuchException:
            payroll_module.remove_payday(paydate, payday_serial)
            book.remove_transaction(payday_trans_id)
            return PAYROLL_VACPAY_DRAW_TOO_MUCH, employee_name 
    
        if emp.has_key('cheque_override'):
            payday.add_cheque_override(emp['name'], emp['cheque_override'])

        #gotta have a net pay line
        if not (1 ==
                len(list(paystub.get_paystub_lines_of_class(
                        PaystubNetPaySummaryLine)))):
            payroll_module.remove_payday(paydate, payday_serial)
            book.remove_transaction(payday_trans_id)
            return PAYROLL_MISSING_NET_PAY, employee_name

        #net pay must be zero or greater than zero, cannot have negative net pay
        net_pay = paystub.net_pay()
        if net_pay < 0:
            sum_ded = Decimal('0')
            total_deductions = paystub.get_deduction_lines()

            for deduct in total_deductions:
                sum_ded += deduct.get_value()

            gross_pay = paystub.gross_income()

            payroll_module.remove_payday(paydate, payday_serial)
            book.remove_transaction(payday_trans_id)
            return (PAYROLL_TOO_MANY_DEDUCTIONS,
                    [employee_name, gross_pay, sum_ded] )
   

    # freeze all calculated paystub lines with current values to avoid
    # unesessary recalculation
    for paystub in payday.paystubs:
        for paystub_line in paystub.get_paystub_lines_of_class(
            PaystubCalculatedLine):
            paystub_line.freeze_value()
    
    print_paystubs(payday, print_paystub_line_config, file_path)
       
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
                yield ( parse_accounting_line_variables(
                        paystub, single_account_line_config[0]),
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
        
    if payday_accounting_lines_balance(payday):
        backend_module = book.get_backend_module()
        backend_module.error_log_file = "bo_keep_backend_error_log"
        backend_module.mark_transaction_dirty(payday_trans_id,
                                              payday)
        backend_module.flush_backend()

        if (display_paystubs):
            print 'spawning oowriter'
            os.spawnv(P_NOWAIT, '/usr/bin/oowriter', ['0', 'PaystubPrint.txt'])
    else:
        payroll_module.remove_payday(paydate, payday_serial)
        book.remove_transaction(payday_trans_id)
        return PAYROLL_ACCOUNTING_LINES_IMBALANCE, None

    print list(book.trans_tree.iteritems())

    return RUN_PAYROLL_SUCCEEDED, None    

def payroll_init(bookname, bookset=None):
    if (bookset == None):
        bookset = BoKeepBookSet( get_database_cfg_file() )

    book = bookset.get_book(bookname)

    payroll_module = payroll_get_payroll_module(bookname, bookset)

    return bookset, book, payroll_module

def payroll_add_employee(bookname, emp_name, bookset=None):
    bookset_close_needed = False
    if bookset == None:
        bookset_close_needed = True

    bookset, book, payroll_module = payroll_init(bookname, bookset)
    if not payroll_module.has_employee(emp_name):
        employee = Employee(emp_name)
        payroll_module.add_employee(emp_name, employee)
        transaction.get().commit()

    if bookset_close_needed:    
        bookset.close()

def payroll_get_employees(bookname, bookset=None):
    bookset, book, payroll_module = payroll_init(bookname, bookset)
    return [payroll_module.get_employees(), bookset]

def payroll_get_employee(bookname, bookset, emp_name):    
    bookset, book, payroll_module = payroll_init(bookname, bookset)
    if payroll_module.has_employee(emp_name):
        return [payroll_module.get_employee(emp_name), bookset]
    else:
        return [None, bookset]

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
        (payday_trans_id, payday) = payroll_module.get_payday(date, serial)
        payroll_module.remove_payday(date, serial)
        book.remove_transaction(payday_trans_id)
        return True
    else:
        return False
    
def payroll_runtime(bookname,
                    ask_user_reprocess=True, display_paystubs=False,
                    bookset=None):
    bookset, book, payroll_module = payroll_init(bookname, bookset)

    add_new_payroll_from_import(book, payroll_module,
                                display_paystubs, ask_user_reprocess)

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

def payroll_add_timesheet(bookname, emp_name, sheet_date, hours, memo,
                          bookset=None):
    #only close the bookset if one wasn't passed in.  If one was passed in then
    #the caller is taking responsibility
    bookset_close_needed = bookset == None
    bookset, book, payroll_module = payroll_init(bookname, bookset)
    if payroll_module.has_employee(emp_name):
        payroll_module.add_timesheet(emp_name, sheet_date, hours, memo)
        transaction.get().commit()
        if bookset_close_needed:
            bookset.close()
        return True
    else:
        if bookset_close_needed:
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
                payroll_add_timesheet(bookname, args[1], d, float(args[3]),
                                      args[4], bookset)
            except ValueError:
                print "I didn't understand your date format.  Please use " \
                    "Month Day, Year (for example 'March 29, 2009'  The " \
                    "spaces are important, I'm a fragile creature who can't" \
                    "understand 'March 29,2009')"
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
            payroll_set_employee_attr(bookname, bookset,
                                      args[0], args[1], args[2])

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
                print "I didn't understand your date format.  Please use " \
                    "Month Day, Year (for example 'March 29, 2009'  The " \
                    "spaces are important, I'm a fragile creature who " \
                    "can't understand 'March 29,2009')"

            if payday == None:
                print "sorry, I couldn't find that payday"
            else:
                print str(payday[1])
    elif command_type == 'drop':
        removed = False
        try:
            #we can add 'drop all' if we want, but that seems kind of dangerous and
            #like something way too easy to do accidentally
            dt = datetime.strptime(args[0], "%B %d, %Y")
            d = date(dt.year, dt.month, dt.day)
            #removed = payroll_remove_payday(bookname, d, int(args[1]), bookset)
        except ValueError:
            print "I didn't understand your date format.  Please use Month " \
                "Day, Year (for example 'March 29, 2009'  The spaces are " \
                "important, I'm a fragile creature who can't understand " \
                "'March 29,2009')"

        if removed == True:
            print 'payday(' + str(dt) + ',' + args[1] + ') dropped.'
        else:
            print "sorry, I couldn't find that payday"
      
    bookset.close()
