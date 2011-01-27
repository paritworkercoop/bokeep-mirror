# functions.py Reuseable functions for all kinds of things
# Copyright (C) 2006 ParIT Worker Co-operative <paritinfo@parit.ca>
# Copyright (C) 2001-2006 Paul Evans <pevans@catholic.org>
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
# Author(s): Mark Jenkins <mark@parit.ca>
#            Paul Evans <pevans@catholic.org>

from bisect import bisect_left
from itertools import ifilter, ifilterfalse, takewhile
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP

# useful with Decimal.quantize
TWOPLACES = Decimal('0.01')
ZEROPLACES = Decimal('1.')

ZERO = Decimal('0.00')

def neg2zero(amount):
    return max(amount, ZERO)

def range_table_lookup(range_table, value_table, value):
    result_index = bisect_left(range_table, value) 
    result = value_table[ result_index ]
    return result

def force_to_tuple(value_or_tuple):
    if type(value_or_tuple) == tuple:
        return value_or_tuple
    else:
        return (value_or_tuple,)

def filter_by_class(filter_class, sequence):
    return ifilter( lambda obj: isinstance(obj, filter_class), sequence)

def filter_by_not_class(filter_class, sequence):
    return ifilterfalse( lambda obj: isinstance(obj, filter_class), sequence)

def instance_of_one(obj, classes):
    for cls in classes:
        if isinstance(obj, cls):
            return True
    return False

def filter_using_tuple( ignore_tuple, iterable):
    if not ignore_tuple.__dict__.has_key('__contains__'):
        ignore_tuple = force_to_tuple(ignore_tuple)
    return ifilterfalse(lambda obj: obj in ignore_tuple,
                        iterable)

def iterate_until_value(iterable, value, include_final_value=False):
    for val in iterable:
        if val == value:
            if include_final_value:
                yield(val)
            break
        else:
            yield(val)


def decimal_round_two_place_using_third_digit(decimal_value):
    # we want these results eh?
    # >>> Decimal('0.025').quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
    # Decimal("0.03")
    # >>> Decimal('0.015').quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
    # Decimal("0.02")
    # >>> Decimal('-0.015').quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
    # Decimal("-0.02")
    # >>> Decimal('-0.025').quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
    # Decimal("-0.03")
    #
    # and this
    # >>> Decimal('0.02499999999999999').quantize(Decimal('0.00'),
    #  rounding=ROUND_HALF_UP)
    # Decimal("0.02")
    #
    # Not this
    # >>> Decimal('0.02499999999999999').quantize(Decimal('0.00'),
    # rounding=ROUND_UP)
    # Decimal("0.03")

    return decimal_value.quantize(TWOPLACES, ROUND_HALF_UP)

def decimal_truncate_two_places(decimal_value):
    """ round something like 0.019 to 0.01 and -0.019 to -0.01
    """
    # note that using ROUND_FLOOR wouldn't achieve the desired results
    # with negative numbers
    return decimal_value.quantize(TWOPLACES, rounding=ROUND_DOWN)

def convert_tuple_of_strings_to_tuple_of_decimals(tuple_of_string):
    return tuple( Decimal(element) for element in tuple_of_string )

def convert_dict_of_string_to_dict_of_decimals_in_place(dict_of_strings):
    """This is an in-place conversion
    """
    for key, value in dict_of_strings.iteritems():
        dict_of_strings[key] = Decimal(value)
