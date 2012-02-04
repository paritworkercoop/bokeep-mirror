# Copyright (C) 2011  ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
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

# gtk imports
from gtk import \
    FileChooserDialog, \
    FILE_CHOOSER_ACTION_SAVE, FILE_CHOOSER_ACTION_OPEN, \
    STOCK_CANCEL, RESPONSE_CANCEL, \
    STOCK_SAVE, RESPONSE_OK, STOCK_OPEN

# bokeep imports
from bokeep.gui.gladesupport.glade_util import \
    load_glade_file_get_widgets_and_connect_signals
from bokeep.util import \
    get_file_in_same_dir_as_module, get_module_for_file_path
from bokeep.gtkutil import file_selection_path
from bokeep.plugins.payroll.csv_dump import do_csv_dump
from bokeep.plugins.payroll.make_T4 import generate_t4s, generate_plain_t4s
from bokeep.plugins.payroll.period_analyse import period_analyse

def get_payroll_glade_file():
    import config as this_module
    return get_file_in_same_dir_as_module(this_module, 'payroll.glade')

def file_selection_module_contents(msg="choose file"):
    file_path = file_selection_path(msg)
    if file_path != None:
        return get_module_for_file_path(file_path)
    return None

class PayrollConfigDialog(object):
    def __init__(self, parent_window, backend_account_fetch, plugin):
        import config as this_module
        load_glade_file_get_widgets_and_connect_signals(
            get_payroll_glade_file(),
            'dialog1', self, self)
        self.backend_account_fetch = backend_account_fetch
        self.plugin = plugin

        if parent_window != None:
            self.dialog1.set_transient_for(parent_window)
            self.dialog1.set_modal(True)
    
    def run(self):
        dia_result = self.dialog1.run()
        if dia_result == RESPONSE_OK:
            pass # we'll need to check this eventually
        self.dialog1.destroy()

    def save_dialog(self, msg):
        fcd = FileChooserDialog(
            msg,
            None,
            FILE_CHOOSER_ACTION_SAVE,
            (STOCK_CANCEL, RESPONSE_CANCEL, STOCK_SAVE, RESPONSE_OK) )
        fcd.set_modal(True)
        result = fcd.run()
        file_path = fcd.get_filename()
        fcd.destroy()
        if result == RESPONSE_OK and file_path != None:
            return file_path
        else:
            return None

    def on_dump_db_clicked(self, *args):
        file_path = self.save_dialog(
        "where should the csv file be saved?")
        if file_path != None:
            do_csv_dump(self.plugin, file_path)

    def t4_dump_stage_one(self, msg):
        t4infomod = file_selection_module_contents(
            "Select the T4 info file")
        if t4infomod == None:
            return None, None

        xml_file_path = self.save_dialog(msg)
        if xml_file_path == None:
            return None,None


        return t4infomod, xml_file_path

    def on_dump_T4_clicked(self, *args):
        t4infomod, xml_file_path = self.t4_dump_stage_one(
            "where should the T4 xml file be saved?")
        if None in (t4infomod, xml_file_path):
            return None

        generate_t4s(xml_file_path, t4infomod.year, self.plugin,
                     t4infomod.extra_attributes_per_employee,
                     t4infomod.summary_attributes,
                     t4infomod.submission_attributes )

    def on_dump_plain_T4_clicked(self, *args):
        t4infomod, xml_file_path = self.t4_dump_stage_one(
            "where should the T4 text file be saved?")
        if None in (t4infomod, xml_file_path):
            return None

        generate_plain_t4s(xml_file_path, t4infomod.year, self.plugin,
                           t4infomod.extra_attributes_per_employee, )

    def on_dump_period_analysis_clicked(self, *args):
        analysis_dia = {}
        load_glade_file_get_widgets_and_connect_signals(        
            get_payroll_glade_file(),
            'dialog2', analysis_dia, None)
        analysis_dia['dialog2'].set_transient_for(self.dialog1)
        analysis_dia['dialog2'].set_modal(True)
        analysis_dia['period_type_pulldown'].set_active(0)
        dia_result = analysis_dia['dialog2'].run()
        if dia_result == RESPONSE_OK:
            output_file_path = self.save_dialog(
                "where should the analysis csv file be saved?")
            if output_file_path != None:
                (start_year, start_month, day) = \
                    analysis_dia['start_date_calendar'].get_date()
                # adjust gtk month convention (0-11) to python 
                # convention (1-12)
                start_month+=1
                
                period_analyse(
                    self.plugin, start_year, start_month,
                    analysis_dia['num_period_spin'].get_value_as_int(),
                    analysis_dia['period_type_pulldown'].get_active_text(),
                    output_file_path)

        analysis_dia['dialog2'].destroy()

    def set_config_file_clicked(self, *args):
        file_path = file_selection_path()
        if file_path != None:
            self.plugin.set_config_file(file_path)
        
