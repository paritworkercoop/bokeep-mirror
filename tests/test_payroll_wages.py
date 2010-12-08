# python imports
import unittest
import os
import shutil
import glob
import filecmp
import sys
from datetime import date
from decimal import Decimal

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
        self.payday = Payday(date(2009, 04, 22), date(2009, 04, 06),
                             date(2009, 04, 19) )
        self.payday_serial = 1
        self.payroll_mod = self.books.get_book(TESTBOOK).get_module(
            PAYROLL_PLUGIN)
        self.bokeep_trans_id = self.books.get_book(TESTBOOK).insert_transaction(
            self.payday)

class wageTestCase(PayrollPaydayTestCaseSetup):     
    def testSinglerun(self):
        result, msg = setup_paystubs_for_payday_from_dicts(
            self.payroll_mod, self.payday_serial, self.bokeep_trans_id,
            self.payday, emp_list, 1, paystub_line_config,
            paystub_accounting_line_config, add_missing_employees=False )
        
        
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
        self.payroll_mod = book.get_module(PAYROLL_PLUGIN)
        self.testSinglerun()
        
if __name__ == "__main__":
    unittest.main()

