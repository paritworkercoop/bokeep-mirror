#!/usr/bin/env python

# python imports
from csv import DictWriter
from sys import argv

# bo-keep imports
from bokeep.config import get_database_cfg_file
from bokeep.book import BoKeepBookSet


PAYROLL_MODULE = 'bokeep.modules.payroll'

def extend_set_with_keys(key_source, key_set):
    for key in key_source.iterkeys():
        key_set.add(key)
    return key_source

def generate_key_for_paystub_line(paystub_line, paystub_dict):
    candidate_key = "%s %s" % (paystub_line.description,
                               paystub_line.__class__ )
    candidate_key_orig = candidate_key
    count = 2
    while candidate_key in paystub_dict:
        candidate_key = "%s %i" % (candidate_key_orig, count)
        count+=1
    return candidate_key

def dictafy_paystub_line(paystub, bokeep_trans_id='', paydate_serial=''):
    paystub_dict = {'employee': paystub.employee.name,
                    'date': str(paystub.payday.paydate),
                    'bo-keep trans id': bokeep_trans_id,
                    'payday serial': paydate_serial }
    for paystub_line in paystub.paystub_lines:
        paystub_dict[
            generate_key_for_paystub_line(
                paystub_line, paystub_dict) ] = paystub_line.get_value()

    return paystub_dict


bookset = BoKeepBookSet( get_database_cfg_file() )
book = bookset.get_book(argv[2])
payroll_mod = book.get_module(PAYROLL_MODULE)

field_list = ['employee', 'date', 'bo-keep trans id', 'payday serial']
new_fields = set(field_list)

# construct a list of all the paystubs associated with all the paydays,
# convert each paystub to a dict representation (see dictafy_paystub_line)
# and track all the keys of all the dicts
paystub_lines_from_payday = [
    extend_set_with_keys(
        dictafy_paystub_line(
            paystub,
            payroll_mod.get_payday(paydate, serial)[0], # arg bokeep_trans_id
            serial),# dictafy_paystub_line
        new_fields ) # extend_set_with_keys
    for paydate, serial in sorted(payroll_mod.get_paydays())
    for paystub in payroll_mod.get_payday(paydate, serial)[1].paystubs
    ] # list comprehension


# contruct a list of all the paystubs associated with each employee
# convert each paystub to a dict representation (see dictafy_paystub_line)
# and track theh the keys of all the dicts
paystub_lines_from_employees = [
    extend_set_with_keys(
        dictafy_paystub_line(
            paystub ),
        new_fields ) # extend_set_with_keys
    for employee_name, employee in sorted(
        payroll_mod.get_employees().iteritems())
    for paystub in employee.paystubs
    ] # list comprehension

# add a sorted list of any new fields we didn't find before
field_list.extend(
    sorted(new_fields.difference( set(field_list) ) ) )

csv_file = file(argv[1], 'wb')
csv_writer = DictWriter(csv_file, field_list )
csv_writer.writerow(
    dict( (field, field) for field in field_list)  )
csv_writer.writerows( paystub_lines_from_payday )

for i in xrange(5):
    csv_writer.writerow( {} )

csv_writer.writerow(
    dict( (field, field) for field in field_list)  )
csv_writer.writerows( paystub_lines_from_employees )

csv_file.close()
