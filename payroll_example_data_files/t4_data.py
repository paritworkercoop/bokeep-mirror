# Technically this file has python "code", but the intent is to just be
# data for end of year T4s you can load and use with the payroll plugin
#
# Unlimited redistribution and modification of this file is permitted
# Original author: ParIT Worker Co-operative <paritinfo@parit.ca>
# You may remove this notice from this file.

from bokeep.plugins.payroll.T619 import PROVINCE_MANITOBA, COUNTRY_CANADA
from bokeep.plugins.payroll.T4 import \
     REPORT_TYPE_CODE_ORIGINAL, TRANS_CODE_SELF_SUBMIT, LANG_CODE_ENGLISH

extra_attributes_per_employee = {
    'Mark Jenkins': dict(
        snm="Jenkins",
        gvn_nm="Mark",
        sin="000000000",
        addr_l1_txt='12 Nobody Strat',
        pstl_cd='R2W1Y5',
        cty_nm="Winnipeg",
        prov_cd=PROVINCE_MANITOBA,
        cntry_cd=COUNTRY_CANADA,
        bn="000000000RP0001",
        ei_xmpt_cd="0",
        cpp_qpp_xmpt_cd="0",
        rpt_tcd=REPORT_TYPE_CODE_ORIGINAL,
        empt_prov_cd=PROVINCE_MANITOBA
        ),
    
    'Joe Hill': dict(
        snm="Hill",
        gvn_nm="Joe",        
        sin="000000000",
        addr_l1_txt='35 Go Away ave',
        pstl_cd='R2W1Y5',
        cty_nm="Winnipeg",
        prov_cd=PROVINCE_MANITOBA,
        cntry_cd=COUNTRY_CANADA,
        bn="000000000RP0001",
        ei_xmpt_cd="0",
        cpp_qpp_xmpt_cd="0",
        rpt_tcd=REPORT_TYPE_CODE_ORIGINAL,
        empt_prov_cd=PROVINCE_MANITOBA
        )
    }

summary_attributes = dict(
    bn="000000000RP0001",
    l1_nm="PARIT WORKER CO-OPERATIVE, LTD",
    addr_l1_txt="57 Al Lane",
    cty_nm="Winnipeg",
    prov_cd=PROVINCE_MANITOBA,
    cntry_cd=COUNTRY_CANADA,
    pstl_cd="R2W1Y5",
    cntc_nm="Mark Jenkins",
    cntc_area_cd="204",
    cntc_phn_nbr="772-5158",
    pprtr_1_sin="000000000",
    rpt_tcd=REPORT_TYPE_CODE_ORIGINAL,
    )

submission_attributes = dict(
    sbmt_ref_id="abcdefgh", # you make it up...
    rpt_tcd=REPORT_TYPE_CODE_ORIGINAL,
    trnmtr_tcd=TRANS_CODE_SELF_SUBMIT,
    trnmtr_nbr="MM555555",
    lang_cd=LANG_CODE_ENGLISH,
    l1_nm="PARIT WORKER CO-OPERATIVE, LTD",
    addr_l1_txt="85 Blah Pl",
    cty_nm="Winnipeg", prov_cd=PROVINCE_MANITOBA,
    cntry_cd=COUNTRY_CANADA, pstl_cd="R2W1Y5",
    cntc_nm="Mark Jenkins", cntc_area_cd="204",
    cntc_phn_nbr="772-5158", cntc_email_area="transparency@parit.ca"
)

year = 2009
