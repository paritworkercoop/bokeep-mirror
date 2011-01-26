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
from bokeep.plugins.payroll.csv_dump import do_csv_dump
from bokeep.plugins.payroll.make_T4 import generate_t4s

def get_payroll_glade_file():
    import config as this_module
    return get_file_in_same_dir_as_module(this_module, 'payroll.glade')

def file_selection_module_contents(msg="choose file"):
    fcd = FileChooserDialog(
        msg,
        None,
        FILE_CHOOSER_ACTION_OPEN,
        (STOCK_CANCEL, RESPONSE_CANCEL, STOCK_OPEN, RESPONSE_OK) )
    fcd.set_modal(True)
    result = fcd.run()
    file_path = fcd.get_filename()
    fcd.destroy()
    if result == RESPONSE_OK and file_path != None:
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

    def on_dump_T4_clicked(self, *args):
        t4infomod = file_selection_module_contents(
            "Select the T4 info file")
        if t4infomod == None:
            return

        xml_file_path = self.save_dialog(
        "where should the T4 xml file be saved?")
        if xml_file_path == None:
            return

        generate_t4s(xml_file_path, t4infomod.year, self.plugin,
                     t4infomod.extra_attributes_per_employee,
                     t4infomod.summary_attributes,
                     t4infomod.submission_attributes )

    def on_dump_period_analysis_clicked(self, *args):
        # select period params
        
        file_path = self.save_dialog(
        "where should the analysis csv file be saved?")
        if file_path == None:
            return

        #magic(self.plugin, period_params, file_path)
