#!/usr/bin/python
from sys import argv

from bokeep.config import get_database_cfg_file
from bokeep.book import BoKeepBookSet
from bokeep.plugins.payroll.plain_text_payroll import \
    payroll_payday_command, payroll_employee_command

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

