#!/usr/bin/env python

# Python library
from sys import argv

# ZODB
import transaction

# Bo-Keep
from bokeep.config import get_database_cfg_file
from bokeep.book import BoKeepBookSet
from bokeep.modules.payroll.payroll import Employee 


def bokeep_main():
    bookset = BoKeepBookSet( get_database_cfg_file() )
    book = bookset.get_book(argv[1])
    payroll_module = book.get_module('bokeep.modules.payroll')

    if argv[2] == "add" and argv[3] == "employee":
        payroll_module.add_employee( argv[4], Employee(argv[4]))
    elif argv[2] == "print" and argv[3] == "employee":
        print str(payroll_module.get_employee( argv[4] ))

    transaction.get().commit()
    bookset.close_primary_connection()

if __name__ == "__main__":
    bokeep_main()

