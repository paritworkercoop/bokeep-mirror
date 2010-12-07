#!/usr/bin/env python

from pyspec_xml import \
     generate_xml, XMLElement, NEW_VISIBLE_CLASS, \
     generate_XML_element_classes_from_shorthand, \
     OPTIONAL_SUB_ELEMENT_CLASSES, OPTIONAL_AUTOMATIC

from T619 import \
     Submission, PROVINCE_MANITOBA, COUNTRY_CANADA, \
     TRANS_CODE_SELF_SUBMIT, REPORT_TYPE_CODE_ORIGINAL, LANG_CODE_ENGLISH

class Return(XMLElement): pass
class T4(XMLElement): pass

generate_XML_element_classes_from_shorthand(
    globals(),
    ["T4Slip", NEW_VISIBLE_CLASS,
     ["EMPE_NM", "snm", "gvn_nm", OPTIONAL_AUTOMATIC, "init"],
     ["EMPE_ADDR",
      "addr_l1_txt", "cty_nm", "prov_cd", "cntry_cd", "pstl_cd"],
     "sin",
     "bn",
     "cpp_qpp_xmpt_cd",
     "ei_xmpt_cd",
     "rpt_tcd",
     "empt_prov_cd",
     ["T4_AMT",
      "empt_incamt",
      OPTIONAL_AUTOMATIC, "cpp_cntrb_amt",
      OPTIONAL_AUTOMATIC, "empe_eip_amt",
      OPTIONAL_AUTOMATIC, "itx_ddct_amt"]
     ], # end T4Slip
    super_class=T4
    )

generate_XML_element_classes_from_shorthand(
    globals(),
    ["T4Summary", NEW_VISIBLE_CLASS,
     "bn",
     ["EMPR_NM", "l1_nm"],
     ["EMPR_ADDR",
      "addr_l1_txt", "cty_nm", "prov_cd", "cntry_cd", "pstl_cd"],
     ["CNTC", "cntc_nm", "cntc_area_cd", "cntc_phn_nbr", ],
     "tx_yr",
     "slp_cnt",
     ["PPRTR_SIN", "pprtr_1_sin"],
     "rpt_tcd",
     ["T4_TAMT",
      "tot_empt_incamt", "tot_empe_cpp_amt", "tot_empe_eip_amt",
      "tot_itx_ddct_amt", "tot_empr_cpp_amt", "tot_empr_eip_amt", 
      ]
     ], # end T4Summary
    super_class=T4
    )

submission_optional_sub_elements = \
    list(Submission.specs[OPTIONAL_SUB_ELEMENT_CLASSES])
submission_optional_sub_elements.append( Return )
submission_specs = list(Submission.specs)
submission_specs[OPTIONAL_SUB_ELEMENT_CLASSES] = \
    submission_optional_sub_elements
Submission.specs = tuple(submission_specs)

Return.setup_element_class_specs(
    Return, element_parents=(Submission,),
    required_sub_element_classes=(T4,) )

T4.setup_element_class_specs(
    T4, element_parents=(Return,),
    optional_sub_element_classes=(T4Slip, T4Summary) )

def main():
    from sys import stdout

    generate_xml( stdout, Submission((
        Return( (
        T4( (
        T4Slip(
        (),
        snm="Jenkins",
        gvn_nm="Mark",
        addr_l1_txt="571 Alfred Ave",
        city_nm="Winnipeg",
        prov_cd=PROVINCE_MANITOBA,
        cntry_cd=COUNTRY_CANADA,
        pstl_cd="R2W1Y5",
        sin="000000000",
        bn="851050526RP0001",
        ei_xmpt_cd="0",
        cpp_qpp_xmpt_cd="0",
        rpt_tcd=REPORT_TYPE_CODE_ORIGINAL,
        empt_prov_cd=PROVINCE_MANITOBA,
        empt_incamt="43",
        cpp_cntrb_amt="2",
        empe_eip_amt="3",
        itx_ddct_amt="5"
        ),

        T4Summary(
        (),
        bn="851050526RP0001",
        l1_nm="PARIT WORKER CO-OPERATIVE, LTD",
        addr_l1_txt="571 Alfred Ave",
        cty_nm="Winnipeg",
        prov_cd=PROVINCE_MANITOBA,
        cntry_cd=COUNTRY_CANADA,
        pstl_cd="R2W1Y5",
        cntc_nm="Mark Jenkins",
        cntc_area_cd="204",
        cntc_phn_nbr="772-5158",
        tx_yr="2007",
        slp_cnt="6",
        pprtr_1_sin="0000000",
        rpt_tcd=REPORT_TYPE_CODE_ORIGINAL,
        tot_empt_incamt="34",
        tot_empe_cpp_amt="3",
        tot_empe_eip_amt="2",
        tot_itx_ddct_amt="0",
        tot_empr_cpp_amt="3",
        tot_empr_eip_amt="3"
        ), # end T4Summary
        ) ), # end T4
        ) ), # end Return
        ),
        sbmt_ref_id="blah", rpt_tcd=REPORT_TYPE_CODE_ORIGINAL,
        trnmtr_nbr="gablah",
        trnmtr_tcd=TRANS_CODE_SELF_SUBMIT, summ_cnt="tablah",
        lang_cd=LANG_CODE_ENGLISH,
        l1_nm="PARIT WORKER CO-OPERATIVE, LTD",
        addr_l1_txt="571 Alfred Ave",
        cty_nm="Winnipeg", prov_cd=PROVINCE_MANITOBA,
        cntry_cd=COUNTRY_CANADA, pstl_cd="R2W1Y5",
        cntc_nm="Mark Jenkins", cntc_area_cd="204",
        cntc_phn_nbr="772-5158", cntc_email_area="mark@parit.ca"
        ))

if __name__ == "__main__":
    main()
