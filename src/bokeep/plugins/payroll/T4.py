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

