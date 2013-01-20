# Technically this file has python "code", but the intent is to just be
# configuration data you can load and use with the payroll plugin
#
# Unlimited redistribution and modification of this file is permitted
# Original author: ParIT Worker Co-operative <paritinfo@parit.ca>
# You may remove this notice from this file.

from bokeep.util import start_of_year

from bokeep.plugins.payroll.payroll import \
    Paystub, PaystubIncomeLine, PaystubCPPDeductionLine, \
    PaystubEIDeductionLine, PaystubCPPDeductionLine, \
    PaystubEmployerContributionLine, PaystubCalculatedIncomeTaxDeductionLine, \
    PaystubCalculatedEmployerContributionLine, \
    PaystubEIEmployerContributionLine, \
    PaystubIncomeLine, PaystubWageLine, \
    PaystubNetPaySummaryLine, \
    PaystubDeductionMultipleOfIncomeLine, \
    PaystubVacpayLine, \
    PaystubDeductionLine, \
    PaystubVacpayPayoutLine, \
    PaystubLine, \
    PaystubCPPEmployerContributionLine,  \
    PaystubIncomeTaxDeductionLine

from bokeep.plugins.payroll.plain_text_payroll import \
    create_paystub_line, \
    create_paystub_wage_line, \
    do_nothing, \
    amount_from_paystub_function, \
    amount_from_paystub_function_reversed, \
    amount_from_paystub_line_of_class, \
    amount_from_paystub_line_of_class_reversed, \
    calculated_value_of_class, \
    lines_of_class_function, \
    value_of_class, \
    create_and_tag_paystub_line, \
    create_and_tag_additional_amount_line, \
    paystub_get_lines_of_class_with_tag, \
    get_lines_of_class_with_tag, \
    sum_line_of_class_with_tag, \
    lines_of_classes_and_not_classes_function, \
    year_to_date_sum_of_class, \
    vacation_pay_rate_on_period_of_paystub

paystub_line_config = (
    ('income', create_paystub_line(PaystubIncomeLine)),
    ('hours', create_paystub_wage_line ),
    ('extra_deduction', create_and_tag_paystub_line(PaystubDeductionLine,
                                              "extra_deduction")),
    ('additional_amount_in_net_pay',
     create_and_tag_additional_amount_line("additional_net_pay_amount") ),
    ('vacation_payout', create_paystub_line(PaystubVacpayPayoutLine)),
)

print_paystub_line_config = [
    ( "hours this period",
      lambda paystub: "%.2f" % sum(
            paystub_line.get_value_components()[0]
            for paystub_line in
            paystub.get_paystub_lines_of_class(PaystubWageLine) )
      ), # tuple
    ( "income",
      amount_from_paystub_function(Paystub.gross_income) ),
    ( "CPP deduction",
      amount_from_paystub_function(Paystub.cpp_deductions) ),
    ( "EI deduction",
      amount_from_paystub_function(Paystub.ei_deductions) ),
    ( "Income tax deduction",
      amount_from_paystub_function(Paystub.income_tax_deductions)),
    ( "extra_deduction", sum_line_of_class_with_tag(
                   PaystubDeductionLine, 'extra_deduction') ),
    ( "total deductions",
      amount_from_paystub_function(Paystub.deductions)  ),
    ( "net payment",
      amount_from_paystub_function(Paystub.net_pay) ),
    ( "employer contributions",
      value_of_class(PaystubCalculatedEmployerContributionLine)),
    ( "vacation pay accrued this period", 
      value_of_class(PaystubVacpayLine)),
    ( "vacation pay rate", vacation_pay_rate_on_period_of_paystub),
    ( "possible vacation payout",
      calculated_value_of_class(PaystubVacpayPayoutLine)),
    ( "actual vacation payout",
      value_of_class(PaystubVacpayPayoutLine)),
    ( "income year to date",
      year_to_date_sum_of_class(PaystubIncomeLine) ),
    ( "cpp (employee) year to date",
      year_to_date_sum_of_class(PaystubCPPDeductionLine) ),
    ( "ei (employee) year to date",
      year_to_date_sum_of_class(PaystubEIDeductionLine) ),
    ( "income tax deducted year to date",
      year_to_date_sum_of_class(PaystubIncomeTaxDeductionLine) ),
    ( "cpp (employer contribution) year to date",
      year_to_date_sum_of_class(PaystubCPPEmployerContributionLine) ),
    ( "ei (employer contribution) year to date",
      year_to_date_sum_of_class(PaystubEIEmployerContributionLine) ),
    ( "hours this year",
      lambda paystub: "%.2f" % sum(
            paystub_line.get_value_components()[0]
            for paystub_line in 
            paystub.employee.get_bounded_paystub_lines_of_class(
                PaystubWageLine,
                start_of_year(paystub.payday.paydate), paystub.payday.paydate,
                paystub, include_final_paystub=True ) )
      ), # tuple

]

CHEQUING_ACCOUNT = ("Assets", "Current Assets", "Checking Account")

payroll_deductions_payment_account = CHEQUING_ACCOUNT
payroll_deductions_liability_account = \
    ("Liabilities", "Payroll Deductions Payable")

paystub_accounting_line_config = [
    # Per employee lines, payroll transaction
    [
        # Debits
        (
            ( ("Expenses", "Payroll Expenses"), "wages",
              lines_of_classes_and_not_classes_function(
                    (PaystubIncomeLine,), (PaystubVacpayPayoutLine,) ) ),
            ( ("Liabilities", "Vacation Pay"),
              "vacation pay",
              lines_of_class_function(PaystubVacpayPayoutLine) ),
            ( ("Liabilities", "Payroll additions clearing"),
              "additional amounts added",
              get_lines_of_class_with_tag(PaystubLine,
                                          "additional_net_pay_amount") ),
            ),
        # Credits
        (
            ( ("Assets", "Payroll extra deductions clearing"),
              "extra_deduction",
              get_lines_of_class_with_tag(PaystubDeductionLine, 
                                          "extra_deduction") ),
            ),
        ],
    # Cummulative lines, payroll transaction
    [
        # Debits
        (
            ( 1, ("Expenses", "Payroll Expenses"), "employer cpp, ei",
              lines_of_class_function(PaystubEmployerContributionLine) ),
            ( 2, ("Expenses", "Payroll Expenses"),
              "vacation pay",
              lines_of_class_function(PaystubVacpayLine) )
        ),
        # Credits
        (
            ( 1, payroll_deductions_liability_account, "employee cpp",
              lines_of_class_function(PaystubCPPDeductionLine) ),
            ( 2, payroll_deductions_liability_account, "employee ei",
              lines_of_class_function(PaystubEIDeductionLine) ),
            ( 3, payroll_deductions_liability_account,
              "employer cpp and ei",
              lines_of_class_function(PaystubEmployerContributionLine) ),
            ( 4, payroll_deductions_liability_account, "income tax",
              lines_of_class_function(PaystubCalculatedIncomeTaxDeductionLine)),
            ( 5, ("Liabilities", "Vacation Pay"),
              "vacation pay",
              lines_of_class_function(PaystubVacpayLine) ),
            ( 6, ("Liabilities", "Payroll temp clearing"), "payment",
              lines_of_class_function(PaystubNetPaySummaryLine) ),
        ),

        ],
    # Per employee transaction lines 
    [
        # Debits
        ( ( ("Liabilities", "Payroll temp clearing"), "payment",
            lines_of_class_function(PaystubNetPaySummaryLine) ),
            
          ),

        # Credits
        ( ( CHEQUING_ACCOUNT, "payment",
            lines_of_class_function(PaystubNetPaySummaryLine) ),
          
          ),

        ],
]
