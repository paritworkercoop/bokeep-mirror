#!/usr/bin/env python
from bokeep.config import get_database_cfg_file
from bokeep.book import BoKeepBookSet

import transaction

from sys import argv

bookset = BoKeepBookSet( get_database_cfg_file() )
book = bookset.get_book(argv[1])
payroll_mod = book.get_module('bokeep.modules.payroll')
all_paystubs = [ paystub
                 
                 for key, (id, payday) in
                 payroll_mod.payday_database.iteritems()
                 for paystub in payday.paystubs ]
for name, employee in payroll_mod.get_employees().iteritems():
    old_len = len(employee.paystubs)
    new_paystubs = [paystub
                    for paystub in employee.paystubs
                    if paystub in all_paystubs ]
    employee.paystubs = new_paystubs
    print name, len(employee.paystubs), old_len

assert (len(all_paystubs) == sum(
    len(employee.paystubs)
    for name, employee in payroll_mod.get_employees().iteritems() ))

assert (set(all_paystubs) == \
        set( paystub 
             for name, employee in payroll_mod.get_employees().iteritems()
             for paystub in employee.paystubs ) )
                             
                          
transaction.get().commit()
bookset.close()
