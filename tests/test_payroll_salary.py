# Copyright (C) 2010  ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
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

import unittest
import os
import shutil
import glob
import filecmp
import sys
from itertools import izip, chain
from decimal import Decimal

# bokeep 
from bokeep.book import BoKeepBookSet
from bokeep.plugins.payroll.payroll import \
    Paystub, PaystubIncomeLine, PaystubCPPDeductionLine, \
    PaystubEIDeductionLine, PaystubCPPDeductionLine, \
    PaystubEmployerContributionLine, PaystubCalculatedIncomeTaxDeductionLine, \
    PaystubCalculatedEmployerContributionLine, \
    PaystubEIEmployerContributionLine, \
    PaystubIncomeLine, \
    PaystubNetPaySummaryLine, \
    PaystubDeductionMultipleOfIncomeLine

from bokeep.plugins.payroll.plain_text_payroll import \
    create_paystub_line, \
    do_nothing, \
    amount_from_paystub_function, \
    amount_from_paystub_function_reversed, \
    amount_from_paystub_line_of_class, \
    amount_from_paystub_line_of_class_reversed, \
    calculated_value_of_class, \
    lines_of_class_function, \
    payroll_runtime, payroll_has_payday, handle_backend_command

from test_bokeep_book import create_filestorage_backed_bookset_from_file
from test_payroll_employee import TESTBOOK
from test_payroll_wages import PayrollPaydayTestCaseSetup

emp_list = [
    dict( name="george costanza",
          income=400.0,
          ),

    dict( name="susie",
          income=800.0,
          ),
]

PARIT_EQUITY_CONSTANT=0.03
PARIT_EQUITY_LIMIT=900

#def add_parit_equity_line(employee, employee_info_dict, paystub, value):
#    equity_line = PaystubDeductionMultipleOfIncomeLine(paystub)
#    equity_line.constant = PARIT_EQUITY_CONSTANT
#    old_equity = sum( ( paystub_line.get_value()
#                        if hasattr(paystub_line, 'parit_equity_deduction')
#                        for paystub_line in paystub
#                        for paystub in employee.paystubs) )

 #   equity_line.parit_equity_deduction = True
    # only add equity line if there is room to deduct for equity
 #   if old_equity < PARIT_EQUITY_LIMIT:
 #       new_equity = old_equity + equity_line.get_value()
 #       if new_equity > PARIT_EQUITY_LIMIT:
 #           equity_line.set_value(PARIT_EQUITY_LIMIT - old_equity)
 #       paystub.add_paystub_line(equity_line)

paystub_line_config = (
    ('income', create_paystub_line(PaystubIncomeLine)),
#    ('equity', add_parit_equity_line),
)


paystub_accounting_line_config = [
    # Per employee lines, payroll transaction
    [
        # Debits
        (
            ( ("Expenses", "Payroll Expenses"), "wages",
              lines_of_class_function(PaystubIncomeLine) ),
            ),
        # Credits
        (),
        ],
    # Cummulative lines, payroll transaction
    [
        # Debits
        (
            ( 1, ("Expenses", "Payroll Expenses"), "employer cpp, ei",
              lines_of_class_function(PaystubEmployerContributionLine) ),
        ),
        # Credits
        (
            ( 1, ("Liabilities", "Payroll Deductions Payable"), "employee cpp",
              lines_of_class_function(PaystubCPPDeductionLine) ),
            ( 2, ("Liabilities", "Payroll Deductions Payable"), "employee ei",
              lines_of_class_function(PaystubEIDeductionLine) ),
            ( 3, ("Liabilities", "Payroll Deductions Payable"),
              "employer cpp and ei",
              lines_of_class_function(PaystubEmployerContributionLine) ),
            ( 4, ("Liabilities", "Payroll Deductions Payable"), "income tax",
              lines_of_class_function(PaystubCalculatedIncomeTaxDeductionLine)),
            ( 5, ("Liabilities", "Payroll payable"), "payment",
              lines_of_class_function(PaystubNetPaySummaryLine) ),
        ),

        ],
    # Per employee transaction lines 
    [
        # Debits
        ( ( ("Liabilities", "Payroll payable"), "payment",
            lines_of_class_function(PaystubNetPaySummaryLine) ),
            
          ),

        # Credits
        ( ( ("Assets", "Chequing account"), "payment",
            lines_of_class_function(PaystubNetPaySummaryLine) ),
          
          ),

        ],
]


class salaryTestCase(PayrollPaydayTestCaseSetup):
    def setUp(self):
        PayrollPaydayTestCaseSetup.setUp(self)
        self.emp_list = emp_list
        self.paystub_line_config = paystub_line_config
        self.paystub_accounting_line_config = paystub_accounting_line_config

    def testSinglerun(self):
        self.perform_single_run()
        transactions = list(self.payday.get_financial_transactions())
        self.assertEquals(len(transactions[0].lines), 8)
        for i in xrange(1, len(transactions)):
            self.assertEquals(len(transactions[i].lines), 2)
        for line, expected_value in izip(
            (line
             for trans in transactions
             for line in trans.lines),
            (
                '400.0', # wage expense
                '800', # wage expense
                '75.15', # employer contribution expense
                '-1031.25', # net pay
                '-75.15', # employer contributions expenses
                '-46.08', # employee cpp
                '-20.76', # employee ei
                '-101.91', # income tax
                '372.69', '-372.69', # george
                '658.56', '-658.56', # susie
                )): 
            self.assertEquals(Decimal(expected_value), line.amount)        
        
    def testDoublerun(self):
        self.testSinglerun()
        self.testSinglerun()

if __name__ == "__main__":
    unittest.main()

