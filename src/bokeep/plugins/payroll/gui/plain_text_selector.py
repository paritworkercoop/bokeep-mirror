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
    RESPONSE_OK, RESPONSE_CANCEL, \
    FILE_CHOOSER_ACTION_OPEN, FileChooserDialog, \
    STOCK_CANCEL, STOCK_OPEN, MessageDialog, BUTTONS_OK

# bokeep imports
from bokeep.gui.gladesupport.glade_util import \
    load_glade_file_get_widgets_and_connect_signals
from bokeep.util import \
    get_file_in_same_dir_as_module, get_module_for_file_path
from bokeep.plugins.payroll.plain_text_payroll import \
    make_print_paystubs_str, setup_paystubs_for_payday_from_dicts, \
    RUN_PAYROLL_SUCCEEDED

class CanadianPayrollEditor(object):
    def __init__(self, *args):
        for i, key in enumerate(
            ('trans', 'transid', 'plugin', 'gui_parent',
             'change_register_function') ):
            setattr(self, key, args[i] )
        import plain_text_selector as this_module
        load_glade_file_get_widgets_and_connect_signals(
            get_file_in_same_dir_as_module(this_module, 'payroll.glade'),
            'window1', self, self)
        self.payrollvbox.reparent(self.gui_parent)
        self.window1.hide()
        
        self.has_config = False
        self.has_data = False
        self.update_paystub_listing()

    def detach(self):
        self.payrollvbox.reparent(self.window1)

    def update_paystub_listing(self):
        buffer_text = ""
        if self.trans.has_accounting_lines_attr():
            if self.has_config:
                buffer_text = make_print_paystubs_str(
                    self.trans, self.print_paystub_line_config)
            else:
                buffer_text = str(self.trans.get_payday_accounting_lines())
                
        self.paystubs_text_view.get_buffer().set_text(buffer_text)
    
    def payroll_data_and_config_changed(self):
        if self.has_config and self.has_data:
            result, msg = setup_paystubs_for_payday_from_dicts(
                self.plugin, self.trans, self.emp_list, self.chequenum_start,
                self.paystub_line_config, self.paystub_accounting_line_config,
                add_missing_employees=True)
            if result != RUN_PAYROLL_SUCCEEDED:
                self.error_dialog("payroll failed with code %s and msg %s"
                                  % (str(result), msg) )
            self.change_register_function()
        self.update_paystub_listing()

    def file_selection_module_contents(self, msg="choose file"):
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

    def error_dialog(self, msg):
        dia = MessageDialog(buttons=BUTTONS_OK,
                            message_format=msg)
        dia.set_modal(True)
        dia.run()
        dia.destroy()

    def on_select_data_clicked(self, *args):
        load_module = self.file_selection_module_contents(
            "select a payday data file")
        self.has_data = (
            load_module != None and 
            hasattr(load_module, 'emp_list') and 
            hasattr(load_module, 'chequenum_start') )

        if self.has_data:
            self.emp_list = load_module.emp_list
            self.chequenum_start = load_module.chequenum_start
            self.trans.set_paydate(load_module.paydate,
                                   load_module.period_start,
                                   load_module.period_end )
            self.payroll_data_and_config_changed()
        else:
            self.error_dialog("Problem with data file")
            
    def on_select_config_clicked(self, *args):
        load_module = self.file_selection_module_contents(
            "select a payroll config file")
        self.has_config = (
            load_module != None and 
            hasattr(load_module, 'paystub_line_config') and
            hasattr(load_module, 'paystub_accounting_line_config') and 
            hasattr(load_module, 'print_paystub_line_config') )

        if self.has_config:
            self.paystub_line_config = load_module.paystub_line_config
            self.paystub_accounting_line_config = \
                load_module.paystub_accounting_line_config
            self.print_paystub_line_config = \
                load_module.print_paystub_line_config
            self.payroll_data_and_config_changed()
        else:
            self.error_dialog("Problem with config file")
