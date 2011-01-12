#!/usr/bin/env python

from sys import argv

from bokeep.config import get_database_cfg_file
from bokeep.book import BoKeepBookSet
from bokeep.plugins.payroll.make_T4 import generate_t4s


from bokeep.plugins.payroll.T619 import PROVINCE_MANITOBA, COUNTRY_CANADA
from bokeep.plugins.payroll.T4 import \
     REPORT_TYPE_CODE_ORIGINAL, TRANS_CODE_SELF_SUBMIT, LANG_CODE_ENGLISH


def main():
    bookset = BoKeepBookSet( get_database_cfg_file() )
                            # book name
    book = bookset.get_book(argv[3])

    extra_attributes_per_employee = {}

    summary_attributes = dict(
        bn="000000000RP0001", # *FIXME*
        l1_nm="PARIT WORKER CO-OPERATIVE, LTD", # *FIXME*
        addr_l1_txt="71 Fred Drive", # *FIXME*
        cty_nm="Winnipeg",
        prov_cd=PROVINCE_MANITOBA, 
        cntry_cd=COUNTRY_CANADA,
        pstl_cd="R2W1Y5", # *FIXME*
        cntc_nm="Mark Jenkins", # *FIXME*
        cntc_area_cd="204", # *FIXME*
        cntc_phn_nbr="772-5158", # *FIXME*
        pprtr_1_sin="000000000", # *FIXME*
        rpt_tcd=REPORT_TYPE_CODE_ORIGINAL,
        )

    submission_attributes = dict(
        sbmt_ref_id="abcdefgh", # you make it up...
        rpt_tcd=REPORT_TYPE_CODE_ORIGINAL,
        trnmtr_tcd=TRANS_CODE_SELF_SUBMIT,
        # this is fine, only some have a transmitter number
        trnmtr_nbr="MM555555",
        lang_cd=LANG_CODE_ENGLISH,
        l1_nm="PARIT WORKER CO-OPERATIVE, LTD", # *FIXME*
        addr_l1_txt="5 Tusk Ave", # *FIXME*
        cty_nm="Winnipeg", prov_cd=PROVINCE_MANITOBA,
        cntry_cd=COUNTRY_CANADA,
        pstl_cd="R2W1Y5", # *FIXME*
        cntc_nm="Mark Jenkins", # *FIXME*
        cntc_area_cd="204", # *FIXME*
        cntc_phn_nbr="772-5158", # *FIXME*
        cntc_email_area="transparency@parit.ca" # *FIXME*
        )

    payroll_module = book.get_module('bokeep.plugins.payroll')
    for employee_name, employee in \
        payroll_module.get_employees().iteritems():
        
        employee_dict = {
            snm=employee.???,
            gvn_nm=employee.????,
            sin=employee.????,
            addr_l1_txt=employee.????,
            pstl_cd=employee.????,
            cty_nm=employee.????, # ussually Winnipeg
            prov_cd=employee.????, # ussually PROVINCE_MANITOBA
            cntry_cd=employee.????, # ussually COUNTRY_CANADA
            bn="000000000RP0001", # *FIXME*
            ei_xmpt_cd="0",
            cpp_qpp_xmpt_cd="0",
            rpt_tcd=REPORT_TYPE_CODE_ORIGINAL,
            empt_prov_cd=PROVINCE_MANITOBA,
            }

        extra_attributes_per_employee[employee_name] = employee_dict
        
                 # file   # year
    generate_t4s(argv[1], int(argv[2]), book,
                 extra_attributes_per_employee,
                 summary_attributes, submission_attributes )
    
    bookset.close()

if __name__ == "__main__":
    main()


