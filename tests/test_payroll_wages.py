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

# python imports
import unittest
import os
import shutil
import glob
import filecmp
import sys
from datetime import date
from decimal import Decimal
from itertools import izip

# zodb import
import transaction

# bokeep payroll imports
from bokeep.plugins.payroll.payroll import \
    Payday, Paystub, PaystubIncomeLine, \
    PaystubEIDeductionLine, PaystubCPPDeductionLine, \
    PaystubEmployerContributionLine, PaystubCalculatedIncomeTaxDeductionLine, \
    PaystubCalculatedEmployerContributionLine, \
    PaystubEIEmployerContributionLine, PaystubCPPEmployerContributionLine, \
    PaystubIncomeLine, \
    PaystubNetPaySummaryLine, \
    PaystubDeductionMultipleOfIncomeLine, \
    PaystubVacpayLine, \
    PaystubDeductionLine
from bokeep.plugins.payroll.plain_text_payroll import \
    create_paystub_line, create_paystub_wage_line, calc_line_override, \
    do_nothing, \
    amount_from_paystub_function, \
    amount_from_paystub_function_reversed, \
    amount_from_paystub_line_of_class, \
    amount_from_paystub_line_of_class_reversed, \
    calculated_value_of_class, \
    lines_of_class_function, \
    create_and_tag_paystub_line, paystub_get_lines_of_class_with_tag, \
    get_lines_of_class_with_tag, sum_line_of_class_with_tag, \
    RUN_PAYROLL_SUCCEEDED, \
    setup_paystubs_for_payday_from_dicts, \
    payroll_employee_command


# bokeep test imports
from test_bokeep_book import create_filestorage_backed_bookset_from_file
from test_payroll_employee import PayrollTestCaseSetup, TESTBOOK, PAYROLL_PLUGIN

emp_list = [
    dict( name="george costanza",
          rate=7.6,
#initialization hours
          hours=84.5
          ),

    dict( name="susie",
          rate=7.6,
#initialization hours
          hours=51.5
          ),
]

paystub_line_config = (
    ('income', create_paystub_line(PaystubIncomeLine) ),
    ('hours', create_paystub_wage_line ),
    ('override_employee_cpp', calc_line_override(PaystubCPPDeductionLine)),
    ('override_employee_ei', calc_line_override(PaystubEIDeductionLine)),
    ('override_employer_cpp',
     calc_line_override(PaystubCPPEmployerContributionLine) ),
    ('override_employer_ei',
     calc_line_override(PaystubEIEmployerContributionLine) ),
    ('override_income_tax',
     calc_line_override(PaystubCalculatedIncomeTaxDeductionLine) ),
    ('override_vacation_pay', calc_line_override(PaystubVacpayLine)),
    ('advance', create_and_tag_paystub_line(PaystubDeductionLine, 
                'advance') ),
)

paystub_accounting_line_config = [
    # Per employee lines, payroll transaction
    [
        # Debits
        (
            ( ("Expenses", "Wages & Benefits", "Wages"), "wages",
              lines_of_class_function(PaystubIncomeLine) ),
            ),
        # Credits
        (),
        ],
    # Cummulative lines, payroll transaction
    [
        # Debits
        (
            ( 1, ("Expenses", "Wages & Benefits", "Wages", "Remittances"),
              "employer contributions to EI, CPP, and WCB",
              lines_of_class_function(PaystubEmployerContributionLine) ),
            ( 2, ("Expenses", "Wages & Benefits", "Wages", "Vacation Pay"),
              "vacation pay",
              lines_of_class_function(PaystubVacpayLine) )
        ),
        # Credits
        (
            ( 1, ("Liabilities", "Payroll Deductions Payable"),
              "cpp deductions",
              lines_of_class_function(PaystubCPPDeductionLine) ),
            ( 2, ("Liabilities", "Payroll Deductions Payable"),
              "ei deductions",
              lines_of_class_function(PaystubEIDeductionLine) ),
            ( 3, ("Liabilities", "Payroll Deductions Payable"),
              "employer contributions to EI, CPP, and WCB",
              lines_of_class_function(PaystubEmployerContributionLine) ),
            ( 4, ("Liabilities", "Payroll Deductions Payable"),
              "income tax deductions",
              lines_of_class_function(PaystubCalculatedIncomeTaxDeductionLine)),
            ( 5, ("Liabilities", "Vacation pay"),
              "vacation pay",
              lines_of_class_function(PaystubVacpayLine) ),
            ( 6, ("Liabilities", "Payroll tmp clearing"),
              "net pay",
              lines_of_class_function(PaystubNetPaySummaryLine) ),
            ( 7, ("Liabilities", "Payroll tmp clearing"), "advances",
              get_lines_of_class_with_tag(PaystubDeductionLine, 
                                          "advance") ),
        ),

        ],
    # Per employee transaction lines 
    [
        # Debits
        ( 
            ( ("Liabilities", "Payroll tmp clearing"), "net pay",
              lines_of_class_function(PaystubNetPaySummaryLine) ),
            ),

        # Credits
        ( 
            ( ("Assets", "ACU - Overhead"), "net pay",
              lines_of_class_function(PaystubNetPaySummaryLine) ),
          
            ),

        ],
]


class PayrollPaydayTestCaseSetup(PayrollTestCaseSetup):
    def setUp(self):
        PayrollTestCaseSetup.setUp(self)
        # implicit bookset.close()
        self.payday = Payday(self.payroll_plugin)
        self.payday.set_paydate(date(2009, 04, 22), date(2009, 04, 06),
                                date(2009, 04, 19) )
        self.payroll_mod = self.books.get_book(TESTBOOK).get_frontend_plugin(
            PAYROLL_PLUGIN)
        self.bokeep_trans_id = self.books.get_book(TESTBOOK).insert_transaction(
            self.payday)
        self.payroll_mod.register_transaction(self.bokeep_trans_id, self.payday)
        self.emp_list = emp_list
        self.paystub_line_config = paystub_line_config
        self.paystub_accounting_line_config = paystub_accounting_line_config

    def perform_single_run(self):
        result, msg = setup_paystubs_for_payday_from_dicts(
            self.payroll_mod,
            self.payday, self.emp_list, 1, self.paystub_line_config,
            self.paystub_accounting_line_config, add_missing_employees=False )
        
        
        self.assertEquals(result, RUN_PAYROLL_SUCCEEDED)
        self.assertEquals(msg, None)
        
        for paystub in self.payday.paystubs:
            for paystub_line in paystub.paystub_lines:
                self.assert_(paystub_line.get_value().as_tuple()[2] >= -2 )
                self.assert_(paystub_line.get_net_value().as_tuple()[2] >= -2 )
                
        transactions = list(self.payday.get_financial_transactions())
        self.assertEquals(3, len(transactions) )
        grand_trans, george_trans, susie_trans = transactions
        # should check of balance of debits and credits, and other things
        # required to pass stringent gnucash other then account spec
        # being right
        for trans in transactions:
            self.assertEquals( Decimal('0.00'),
                               sum( line.amount for line in trans.lines ) )
            for line in trans.lines:
                self.assert_(line.amount.as_tuple()[2] >= -2 )

        transaction.get().commit()

class wageTestCase(PayrollPaydayTestCaseSetup):     
    def testSinglerun(self):
        self.perform_single_run()
        transactions = list(self.payday.get_financial_transactions())
        self.assertEquals(len(transactions[0].lines), 11)
        for i in xrange(1, len(transactions)):
            self.assertEquals(len(transactions[i].lines), 2)
        for line, expected_value in izip(
            (line
             for trans in transactions
             for line in trans.lines),
            (
                '642.20', # wage expense
                '391.40', # wage expense
                '62.87', # employer contribution expense
                '41.35', # vacation pay
                '-37.84', # employee cpp
                '0.00', # advance
                '-41.35', # vacation pay accured
                '-914.83', # net pay
                '-63.05', # income tax
                '-17.88', # employee ei
                '-62.87', # employer contributions expenses
                '549.29', '-549.29', # george
                '365.54', '-365.54', # susie
                )): 
            self.assertEquals(Decimal(expected_value), line.amount)
        
    def testDoublerun(self):
        self.testSinglerun()
        self.testSinglerun()


    def testTimesheeting(self):
        self.testSinglerun()
        self.books.close()
        self.books = create_filestorage_backed_bookset_from_file(
            self.filestorage_file, False)

        for payroll_info_list in (
            ["timesheet", "george costanza", "April 5, 2009", 20,
             "12-8 server"],
            ["timesheet", "george costanza", "April 6, 2009", 30,
             "morning admin"],
            ["timesheet", "susie", "April 7, 2009", 15, "morning line"],
            ["timesheet", "george costanza", "April 8, 2009", 12, "evening sf"],
            ["timesheet", "susie", "April 8, 2009", 5, "morning sf"],
            ["timesheet", "george costanza", "April 19, 2009", 4, "misc"],
            ["timesheet", "susie", "April 19, 2009", 4, "extra labour"],
            ["timesheet", "susie", "April 20, 2009", 15, "morning grocery"] ):

            payroll_employee_command(TESTBOOK, self.books, "add",
                                     payroll_info_list )
            # implicit bookset.close()
            self.books = create_filestorage_backed_bookset_from_file(
                self.filestorage_file, False)

        book = self.books.get_book(TESTBOOK)
        self.payday = book.get_transaction(self.bokeep_trans_id)
        self.payroll_mod = book.get_frontend_plugin(PAYROLL_PLUGIN)

        # copy the main emp_list
        self.emp_list = [ dict(info_dict) for info_dict in emp_list ]
        for employee_dict in self.emp_list:
            employee = self.payroll_mod.get_employee(employee_dict['name'])
            # start sum with existing hours outside of timesheet
            employee_dict['hours'] = sum(
                ( timesheet.hours
                  for timesheet in employee.get_timesheets(
                        self.payday.period_start,
                        self.payday.period_end ) ),
                employee_dict['hours'] )

        self.perform_single_run()
        transactions = list(self.payday.get_financial_transactions())
        self.assertEquals(len(transactions[0].lines), 11)
        for i in xrange(1, len(transactions)):
            self.assertEquals(len(transactions[i].lines), 2)
        for line, expected_value in izip(
            (line
             for trans in transactions
             for line in trans.lines),
            (
                '991.80', # wage expense
                '573.80', # wage expense
                '102.09', # employer contribution expense
                '62.62', # vacation pay
                '-64.17', # employee cpp
                '0.00', # advance
                '-62.62', # vacation pay accured
                '-1293.30', # net pay
                '-181.04', # income tax
                '-27.09', # employee ei
                '-102.09', # employer contributions expenses
                '791.37', '-791.37', # george
                '501.93', '-501.93', # susie
                )): 
            self.assertEquals(Decimal(expected_value), line.amount)        
        
if __name__ == "__main__":
    unittest.main()

