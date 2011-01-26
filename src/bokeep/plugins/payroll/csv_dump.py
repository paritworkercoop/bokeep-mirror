# Copyright (C) 2011  ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
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

# python imports
from csv import DictWriter
from sys import argv

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

def dictafy_paystub_line(paystub, bokeep_trans_id=''):
    paystub_dict = {'employee': paystub.employee.name,
                    'date': str(paystub.payday.paydate),
                    'bo-keep trans id': bokeep_trans_id,
                     }
    for paystub_line in paystub.paystub_lines:
        paystub_dict[
            generate_key_for_paystub_line(
                paystub_line, paystub_dict) ] = paystub_line.get_value()

    return paystub_dict


def do_csv_dump(payroll_mod, csv_file_path):

    field_list = ['employee', 'date', 'bo-keep trans id']
    new_fields = set(field_list)

    # construct a list of all the paystubs associated with all the paydays,
    # convert each paystub to a dict representation (see dictafy_paystub_line)
    # and track all the keys of all the dicts
    paystub_lines_from_payday = [
        extend_set_with_keys(
            dictafy_paystub_line(
                paystub,
                trans_id, # arg bokeep_trans_id
                ),# dictafy_paystub_line
            new_fields ) # extend_set_with_keys
        for trans_id, payday in payroll_mod.get_paydays().iteritems()
        for paystub in payday.paystubs
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

    csv_file = file(csv_file_path, 'wb')
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
