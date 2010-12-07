#!/usr/bin/env python

from datetime import date

from T4 import \
     Submission, generate_xml, T4, Return, T4Slip, T4Summary

from cdnpayroll.paystub_line import PaystubIncomeLine
from cdnpayroll.cpp import \
    PaystubCPPDeductionLine, PaystubCPPEmployerContributionLine
from cdnpayroll.ei import \
    PaystubEIDeductionLine, PaystubEIEmployerContributionLine
from cdnpayroll.income_tax import PaystubIncomeTaxDeductionLine

def DerivedT4Summary(t4s, **kargs):
    NUM_TOTS = 4
    tots = [0.0 for x in xrange(NUM_TOTS) ]
    emp_strings = ("empt_incamt", "cpp_cntrb_amt", "empe_eip_amt",
                   "itx_ddct_amt")
    tot_strings = ["tot_empt_incamt", "tot_empe_cpp_amt",
                   "tot_empe_eip_amt", "tot_itx_ddct_amt" ]
    
    assert( len(tots) == NUM_TOTS and len(emp_strings) == NUM_TOTS)
    for t4 in t4s:
        for i, emp_string in enumerate(emp_strings):
            if emp_string in t4.init_args:
                tots[i] += float(t4.init_args[emp_string])
    for i, tot_string in enumerate(tot_strings):
        kargs[tot_string] = "%.2f" % tots[i]
        
    return T4Summary((), **kargs)

def get_year_boundaries(year):
    return date(year, 1, 1), date(year, 12, 31)

def generate_t4_for_employee(employee, year, extra_attributes):
    start_of_year, end_of_year = get_year_boundaries(year)

    def get_class_sum_for_employee(employee, cls):
        return "%.2f" % employee.get_bounded_sum_of_paystub_line_class(
            cls, start_of_year, end_of_year, None, True)

    if 'ei_xmpt_cd' not in extra_attributes:
        extra_attributes['ei_xmpt_cd'] = '0'
    if 'cpp_qpp_xmpt_cd' not in extra_attributes:
        extra_attributes['cpp_qpp_xmpt_cd'] = '0'

    ei_sum = get_class_sum_for_employee(employee, PaystubEIDeductionLine)
    if round(float(ei_sum), 2) != 0.00:
        extra_attributes['empe_eip_amt'] = ei_sum

    cpp_sum = get_class_sum_for_employee(employee, PaystubCPPDeductionLine)
    if round(float(cpp_sum), 2) != 0.00:
        extra_attributes['cpp_cntrb_amt'] = cpp_sum

    income_tax_sum = get_class_sum_for_employee(
        employee, PaystubIncomeTaxDeductionLine)
    if round(float(income_tax_sum), 2) != 0.00:
        extra_attributes['itx_ddct_amt'] = income_tax_sum

    return T4Slip(
        (),
        empt_incamt=get_class_sum_for_employee(
            employee, PaystubIncomeLine),
        **extra_attributes )

def generate_t4s(
    t4_file_name, year, book, extra_attributes_per_employee,
    summary_attributes, submission_attributes ):

    payroll_module = book.get_module('bokeep.plugins.payroll')


    xml_output_file = file(t4_file_name, 'w')

    t4parts = [
        generate_t4_for_employee(
            employee, year, extra_attributes_per_employee[employee_name] )
        for employee_name, employee in
        payroll_module.get_employees().iteritems()
        ]

    start_of_year, end_of_year = get_year_boundaries(year)

    def total_up_employer_contributions(cls):
        return "%.2f" % sum(
            emp.get_bounded_sum_of_paystub_line_class(
                cls, start_of_year, end_of_year, None, True)
            for emp in payroll_module.get_employees().itervalues() )

    t4summary = DerivedT4Summary(
        t4parts,
        tx_yr=str(year),
        slp_cnt=str(len(extra_attributes_per_employee)),
        tot_empr_eip_amt=total_up_employer_contributions(
            PaystubEIEmployerContributionLine),
        tot_empr_cpp_amt=total_up_employer_contributions(
            PaystubCPPEmployerContributionLine),
        **summary_attributes
        )

    t4parts.append(t4summary)


    generate_xml( xml_output_file,
                  Submission( (
                Return( ( T4( t4parts ),) ), # end return
                ),
                              summ_cnt="1", # only one summary
                              **submission_attributes
                              ) # end Submission
                  ) # end generate_xml

    xml_output_file.close()
