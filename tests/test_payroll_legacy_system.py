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
from unittest import main
from datetime import date
from os import mkdir

# bokeep imports
from bokeep.plugins.payroll.plain_text_payroll import \
    payroll_add_employee, add_new_payroll, \
    RUN_PAYROLL_SUCCEEDED, \
    create_paystub_line, create_paystub_wage_line, calc_line_override, \
    do_nothing, \
    amount_from_paystub_function, \
    amount_from_paystub_function_reversed, \
    amount_from_paystub_line_of_class, \
    amount_from_paystub_line_of_class_reversed, \
    calculated_value_of_class, \
    lines_of_class_function, value_of_class, \
    lines_of_classes_and_not_classes_function, \
    create_and_tag_paystub_line, sum_line_of_class_with_tag, \
    paystub_get_lines_of_class_with_tag, get_lines_of_class_with_tag, \
    get_ytd_sum_of_class, amount_from_paystub_line_of_class

from bokeep.plugins.payroll.payroll import \
    Paystub, PaystubIncomeLine, \
    PaystubEIDeductionLine, PaystubCPPDeductionLine, \
    PaystubEmployerContributionLine, PaystubCalculatedIncomeTaxDeductionLine, \
    PaystubCalculatedEmployerContributionLine, \
    PaystubEIEmployerContributionLine, PaystubCPPEmployerContributionLine, \
    PaystubIncomeLine, \
    PaystubNetPaySummaryLine, \
    PaystubDeductionMultipleOfIncomeLine, \
    PaystubVacpayLine, \
    PaystubVacpayPayoutLine, \
    PaystubVacationPayAvailable, \
    PaystubWageLine, \
    PaystubDeductionLine


# bokeep test imports
from test_gnucash_backend import \
    GnuCashBasicSetup, BANK_FULL_SPEC, PETTY_CASH_FULL_SPEC
from test_bokeep_book import BoKeepWithBookSetup, TESTBOOK, create_tmp_filename


BACKEND_PLUGIN = 'bokeep.backend_plugins.gnucash_backend'
PAYROLL_PLUGIN = 'bokeep.plugins.payroll'

def create_paystub_child_line(employee, employee_info_dict, paystub, value):
#    cb_rate = 0.0
#    return employee_info_dict._rate

    paystub.add_paystub_line(PaystubWageLine(paystub,
                                             employee_info_dict['childbenefit'],
                                             employee.rate ) )

def create_capped_tagged_deduction_line(tag):
    def return_function(employee, employee_info_dict, paystub, value):
        new_paystub_line = PaystubDeductionLine(paystub, value)
        setattr(new_paystub_line, tag, None)

        net_pay_lines = paystub.get_paystub_lines_of_class(PaystubNetPaySummaryLine)
        total_net_pay = Decimal(0)
        for line in net_pay_lines:
            total_net_pay += line.get_calculated_value()

        #in error conditions, such as too many deductions, net pay can be 
        #LESS than zero.  If that's the case, keep this deduction line at zero
        if total_net_pay <= Decimal('0'):
            new_paystub_line = PaystubDeductionLine(paystub, Decimal('0'))
            setattr(new_paystub_line, tag, None)
        elif total_net_pay < Decimal(str(value)):
            new_paystub_line = PaystubDeductionLine(paystub, total_net_pay)
            setattr(new_paystub_line, tag, None)

        paystub.add_paystub_line(new_paystub_line)
    return return_function

paystub_line_config = (
    ('income', create_paystub_line(PaystubIncomeLine) ),
    ('hours', create_paystub_wage_line ),
    ('vacpaydraw', create_and_tag_paystub_line(PaystubVacpayPayoutLine, 'vacpaydraw')),
    ('childbenefit', create_paystub_child_line ),    
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
    ('equity', create_capped_tagged_deduction_line('equity')),
)

print_paystub_line_config = [
    ( "income",
      amount_from_paystub_function(Paystub.gross_income) ),
    ( "CPP deduction",
      amount_from_paystub_function(Paystub.cpp_deductions) ),
    ( "EI deduction",
      amount_from_paystub_function(Paystub.ei_deductions) ),
    ( "Income tax deduction",
      amount_from_paystub_function(Paystub.income_tax_deductions)),
    ( "advance", sum_line_of_class_with_tag(
                   PaystubDeductionLine, 'advance') ),
    ( "total deductions",
      amount_from_paystub_function(Paystub.deductions)  ),
    ( "net payment",
      amount_from_paystub_function(Paystub.net_pay) ),
    ( "employer contributions",
      value_of_class(PaystubCalculatedEmployerContributionLine)),
    ( "vacation pay drawn this period",
      value_of_class(PaystubVacpayPayoutLine)),
    ( "vacation pay accrued this period", 
      value_of_class(PaystubVacpayLine)),        
]

paystub_accounting_line_config = [
    # Per employee lines, payroll transaction
    [
        # Debits
        (
            ( BANK_FULL_SPEC, "wages",
              lines_of_class_function(PaystubIncomeLine) ),
            ),
        # Credits
        (
            ( BANK_FULL_SPEC, "equity",
              get_lines_of_class_with_tag(PaystubDeductionLine, 
                                          "equity") ),
        ),
        ],
    # Cummulative lines, payroll transaction
    [
        # Debits
        (
            ( 1, BANK_FULL_SPEC,
              "employer contributions to EI, CPP, and WCB",
              lines_of_class_function(PaystubEmployerContributionLine) ),
            ( 2, BANK_FULL_SPEC,
              "vacation pay",
              lines_of_class_function(PaystubVacpayLine) )
        ),  
        # Credits
        (
            ( 1, BANK_FULL_SPEC,
              "cpp deductions",
              lines_of_class_function(PaystubCPPDeductionLine) ),
            ( 2, BANK_FULL_SPEC,
              "ei deductions",
              lines_of_class_function(PaystubEIDeductionLine) ),
            ( 3, BANK_FULL_SPEC,
              "employer contributions to EI, CPP, and WCB",
              lines_of_class_function(PaystubEmployerContributionLine) ),
            ( 4, BANK_FULL_SPEC,
              "income tax deductions",
              lines_of_class_function(PaystubCalculatedIncomeTaxDeductionLine)),
            ( 5, BANK_FULL_SPEC,
              "vacation pay",
              lines_of_class_function(PaystubVacpayLine) ),
            ( 6, BANK_FULL_SPEC,
              "net pay",
              lines_of_class_function(PaystubNetPaySummaryLine) ),
            ( 7, BANK_FULL_SPEC, "advances",
              get_lines_of_class_with_tag(PaystubDeductionLine, 
                                          "advance") ),
        ),

        ],
    # Per employee transaction lines 
    [
        # Debits
        ( 
            ( BANK_FULL_SPEC, "net pay",
              lines_of_class_function(PaystubNetPaySummaryLine) ),
            ( BANK_FULL_SPEC, "advances", 
              get_lines_of_class_with_tag(PaystubDeductionLine, "advance")),
            ),

        # Credits
        ( 
            ( BANK_FULL_SPEC, "net pay",
              lines_of_class_function(PaystubNetPaySummaryLine) ),

            ( BANK_FULL_SPEC, "advances", 
              get_lines_of_class_with_tag(PaystubDeductionLine, "advance")), 
            ),

        ],
]
class BoKeepPayrollLegacyTest(BoKeepWithBookSetup, GnuCashBasicSetup):
    def setUp(self):
        BoKeepWithBookSetup.setUp(self)
        
        # set up GnuCash backend plugin
        GnuCashBasicSetup.setUp(self)

        self.backend_module.close()
        self.test_book_1.set_backend_module(BACKEND_PLUGIN)
        self.backend_module = self.test_book_1.get_backend_module()
        self.backend_module.setattr(
            'gnucash_file', self.get_gnucash_file_name_with_protocol() )

        self.test_book_1.add_module(PAYROLL_PLUGIN)
        self.test_book_1.enable_module(PAYROLL_PLUGIN)
        self.payroll_plugin = self.test_book_1.get_module(PAYROLL_PLUGIN)

        payroll_add_employee(TESTBOOK, 'Elmer Fud', self.books)
        

    def test_basis_payroll_run(self):
        period_end = period_start = paydate = date(2010, 10, 1)
        emp_list = [
            {
                'name': 'Elmer Fud',
                'hours': 2.0,
                },
            ]
        # should perhaps clean this up in tearDown
        file_path = create_tmp_filename("log_dir", "")
        mkdir(file_path)
        code, msg = add_new_payroll(
            self.test_book_1, self.payroll_plugin, False, paydate,
            emp_list, 1, period_start,
            period_end, paystub_line_config,
            paystub_accounting_line_config,
            print_paystub_line_config, file_path ) 
        self.assertEquals( RUN_PAYROLL_SUCCEEDED, code)

    def tearDown(self):
        GnuCashBasicSetup.tearDown(self)
        BoKeepWithBookSetup.tearDown(self)
        
        
if __name__ == "__main__":
    main()

