"""
the lib bokeep.bo_keep_payroll was never meant to be a library, it was an
application for inputting a payroll via a plain text method.

The library functionality that ended up in it has been moved to
bo-keep.modules.payroll.plain_text_payroll, and the application script
(bo_keep_payroll.py) simplified to use that.

So, this file is deprecated. For transition's sake, it imports all of
the symbols that were moved to plain_text_payroll. Please switch
your imports to:
from bokeep.modules.payroll.plain_text_payroll import blah

This file will be removed in a future version,
any attempt to from bokeep.bo_keep_payroll import blah will break
"""

from bokeep.modules.payroll.plain_text_payroll import \
    PAYROLL_MODULE, RUN_PAYROLL_SUCCEEDED, PAYROLL_ALREADY_EXISTS, \
    PAYROLL_ACCOUNTING_LINES_IMBALANCE, PAYROLL_MISSING_NET_PAY, \
    PAYROLL_TOO_MANY_DEDUCTIONS, PAYROLL_DATABASE_MISSING_EMPLOYEE, \
    PAYROLL_VACPAY_DRAW_TOO_MUCH, \
    payroll_succeeded, payroll_already_exists, \
    payroll_accounting_lines_imbalance, print_paystub, print_paystubs, \
    payday_accounting_lines_balance, add_new_payroll_from_import, \
    add_new_payroll, \
    payroll_init, payroll_add_employee, payroll_get_employees, \
    payroll_get_employee, payroll_get_paydays, payroll_get_payday, \
    payroll_remove_payday, payroll_runtime, payroll_has_payday_serial, \
    payroll_run_main, payroll_set_employee_attr, \
    payroll_set_all_employee_attr, payroll_add_timesheet, \
    payroll_get_payroll_module, payroll_employee_command, \
    payroll_payday_command


