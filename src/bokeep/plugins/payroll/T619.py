# Copyright (C)  2008 ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
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

from pyspec_xml import \
     generate_xml, AttributeSpec, ParentScrapingXMLElement, \
     NEW_VISIBLE_CLASS, generate_XML_element_classes_from_shorthand, \
     OPTIONAL_SUB_ELEMENT_CLASSES, OPTIONAL_AUTOMATIC

REPORT_TYPE_CODE_ORIGINAL = 'O'
REPORT_TYPE_CODE_AMENDED = 'A'
REPORT_TYPE_CODE_CANCEL = 'C'

TRANS_CODE_SELF_SUBMIT, TRANS_CODE_SUBMIT_FOR_OTHERS, \
TRANS_CODE_SUBMIT_SOFTPACK, TRANS_CODE_SUBMIT_SOFTVEND = range(1, 4+1)

LANG_CODE_ENGLISH = 'E'
LANG_CODE_FRENCH  = 'F'

PROVINCE_MANITOBA = "MB"
COUNTRY_CANADA = "CAN"
COUNTRY_USA = "USA"

generate_XML_element_classes_from_shorthand(
    globals(),
    [ "Submission",
      NEW_VISIBLE_CLASS,
      AttributeSpec("noNamespaceSchemaLocation",
                    default="layout-topologie.xsd",
                    prefix="xsi",
                    uri="http://www.w3.org/2001/XMLSchema-instance" ),
        ["T619",
         "sbmt_ref_id", "rpt_tcd", "trnmtr_nbr",
         "trnmtr_tcd",
         "summ_cnt", "lang_cd",

         ["TRNMTR_NM",
          "l1_nm", 
          ], # end TRNMTR_NM
          ["TRNMTR_ADDR",
           "addr_l1_txt", "cty_nm", "prov_cd",
           "cntry_cd", "pstl_cd"
           ], # end TRNMTR_ADDR
          ["CNTC", NEW_VISIBLE_CLASS,
           "cntc_nm", "cntc_area_cd", "cntc_phn_nbr", "cntc_email_area"
           ], # end CNTC
         ] # end T619
      ] # end Submission
    )

#class cntc_extra(ParentScrapingXMLElement): pass

#cntc_extra.setup_simple_scraper_specs(
#    cntc_extra, "cntc_extra", CNTC, parent_level=3, mandatory=False)

#cntc_optional_sub_elements = list(CNTC.specs[OPTIONAL_SUB_ELEMENT_CLASSES])
#ctnc_optional_sub_elements.append( cntc_extra )
#CNTC.specs[OPTIONAL_SUB_ELEMENT_CLASSES] = cntc_optional_sub_elements


def main():
    from sys import stdout
    generate_xml( stdout, Submission(
        (),
        sbmt_ref_id="blah", rpt_tcd=REPORT_TYPE_CODE_ORIGINAL,
        trnmtr_nbr="gablah",
        trnmtr_tcd=TRANS_CODE_SELF_SUBMIT, summ_cnt="1",
        lang_cd=LANG_CODE_ENGLISH,
        l1_nm="ParIT Worker Co-operative, Ltd",
        addr_l1_txt="34 Woot Ave",
        cty_nm="Winnipeg", prov_cd=PROVINCE_MANITOBA,
        cntry_cd=COUNTRY_CANADA, pstl_cd="R2W1Y5",
        cntc_nm="Mark Jenkins", cntc_area_cd="204",
        cntc_phn_nbr="772-5158", cntc_email_area="mark@parit.ca"
        ) )

    
if __name__ == "__main__":
    main()
