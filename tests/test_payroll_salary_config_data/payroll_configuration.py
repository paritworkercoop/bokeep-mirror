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
    lines_of_class_function

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
        ( ( ("Assets", "Chequing account"), "payment",
            lines_of_class_function(PaystubNetPaySummaryLine) ),
          
          ),

        ],
]
