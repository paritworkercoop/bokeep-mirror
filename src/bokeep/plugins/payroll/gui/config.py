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
from gtk import RESPONSE_OK

# bokeep imports
from bokeep.gui.gladesupport.glade_util import \
    load_glade_file_get_widgets_and_connect_signals
from bokeep.util import get_file_in_same_dir_as_module

def get_payroll_glade_file():
    import config as this_module
    return get_file_in_same_dir_as_module(this_module, 'payroll.glade')

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

    def on_dump_DB_clicked(self, *args):
        pass

    def on_dump_T4_clicked(self, *args):
        pass

    def on_dump_period_analysis_clicked(self, *args):
        pass
