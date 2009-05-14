from bokeep.modules.payroll.payroll import \
    Paystub, PaystubIncomeLine, PaystubCPPDeductionLine, \
    PaystubEIDeductionLine, PaystubCPPDeductionLine, \
    PaystubEmployerContributionLine, PaystubCalculatedIncomeTaxDeductionLine, \
    PaystubCalculatedEmployerContributionLine, \
    PaystubEIEmployerContributionLine, \
    PaystubIncomeLine, \
    PaystubNetPaySummaryLine, \
    PaystubDeductionMultipleOfIncomeLine, \
    PaystubVacpayLine, \
    PaystubDeductionLine

from bokeep.modules.payroll.plain_text_payroll import \
    create_paystub_line, \
    create_paystub_wage_line, \
    do_nothing, \
    amount_from_paystub_function, \
    amount_from_paystub_function_reversed, \
    amount_from_paystub_line_of_class, \
    amount_from_paystub_line_of_class_reversed, \
    calculated_value_of_class, \
    lines_of_class_function

def create_and_tag_paystub_line(paystub_line_class, tag):
    def return_function(employee, employee_info_dict, paystub, value):
        new_paystub_line = paystub_line_class(paystub, value)
        setattr(new_paystub_line, tag, None)
        paystub.add_paystub_line(new_paystub_line)
    return return_function

def paystub_get_lines_of_class_with_tag(
    paystub, paystub_line_class, tag):
    return ( line
             for line in paystub.get_paystub_lines_of_class(
                 paystub_line_class)
             if hasattr(line, tag) )

def get_lines_of_class_with_tag(paystub_line_class, tag):
    def return_function(paystub):
        return paystub_get_lines_of_class_with_tag(
            paystub, paystub_line_class, tag)
    return return_function

def sum_line_of_class_with_tag(paystub_line_class, tag):
    def return_function(paystub):
        return sum( 
            ( line.get_value()
              for line in paystub_get_lines_of_class_with_tag(
                  paystub, paystub_line_class, tag)
            ), # end generator
            0.0) # end sum
    return return_function


paystub_line_config = (
    ('income', create_paystub_line(PaystubIncomeLine)),
    ('hours', create_paystub_wage_line ),
    ('extra_deduction', create_and_tag_paystub_line(PaystubDeductionLine,
                                              "extra_deduction"))
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
    ( "extra_deduction", sum_line_of_class_with_tag(
                   PaystubDeductionLine, 'extra_deduction') ),
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
            ( 1, ("Expenses", "Payroll Expenses"), "employer cpp, ei",
              lines_of_class_function(PaystubEmployerContributionLine) ),
            ( 2, ("Expenses", "Payroll Expenses"),
              "vacation pay",
              lines_of_class_function(PaystubVacpayLine) )
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
            ( 5, ("Liabilities", "Vacation Pay"),
              "vacation pay",
              lines_of_class_function(PaystubVacpayLine) ),
            ( 6, ("Liabilities", "Payroll temp clearing"), "payment",
              lines_of_class_function(PaystubNetPaySummaryLine) ),
            ( 7, ("Liabilities", "Payroll extra deductions clearing"),
              "extra_deduction",
              get_lines_of_class_with_tag(PaystubDeductionLine, 
                                          "extra_deduction") ),
        ),

        ],
    # Per employee transaction lines 
    [
        # Debits
        ( ( ("Liabilities", "Payroll temp clearing"), "payment",
            lines_of_class_function(PaystubNetPaySummaryLine) ),
            
          ),

        # Credits
        ( ( ("Assets", "Current Assets", "Checking Account"), "payment",
            lines_of_class_function(PaystubNetPaySummaryLine) ),
          
          ),

        ],
]
