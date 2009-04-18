from bokeep.modules.payroll.payroll import \
    Paystub, PaystubIncomeLine, PaystubCPPDeductionLine, \
    PaystubEIDeductionLine, PaystubCPPDeductionLine, \
    PaystubEmployerContributionLine, PaystubCalculatedIncomeTaxDeductionLine, \
    PaystubCalculatedEmployerContributionLine, \
    PaystubEIEmployerContributionLine, \
    PaystubIncomeLine, \
    PaystubNetPaySummaryLine, \
    PaystubDeductionMultipleOfIncomeLine

from bokeep.modules.payroll.plain_text_payroll import \
    create_paystub_line, \
    do_nothing, \
    amount_from_paystub_function, \
    amount_from_paystub_function_reversed, \
    amount_from_paystub_line_of_class, \
    amount_from_paystub_line_of_class_reversed, \
    calculated_value_of_class, \
    lines_of_class_function

paystub_line_config = (
    ('income', create_paystub_line(PaystubIncomeLine)),
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
    ( "total deductions",
      amount_from_paystub_function(Paystub.deductions)  ),
    ( "net payment",
      amount_from_paystub_function(Paystub.net_pay) ),
    ( "employer contributions",
      calculated_value_of_class(PaystubCalculatedEmployerContributionLine)),
]


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
            ( 1, ("Expenses", "Payroll Expenses"), "wages",
              lines_of_class_function(PaystubIncomeLine) ),
            ( 2, ("Expenses", "Payroll Expenses"), "employer cpp, ei",
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
        ( ( ("Assets", "Current Assets", "Checking Account"), "payment",
            lines_of_class_function(PaystubNetPaySummaryLine) ),
          
          ),

        ],
]
