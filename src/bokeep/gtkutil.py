# Copyright (C) 2010  ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
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

def file_selection_path(msg="choose file"):   
    fcd = FileChooserDialog(
        msg,
        None,
        FILE_CHOOSER_ACTION_OPEN,
        (STOCK_CANCEL, RESPONSE_CANCEL, STOCK_OPEN, RESPONSE_OK) )
    fcd.set_modal(True)
    result = fcd.run()
    file_path = fcd.get_filename()
    fcd.destroy()
    if result == RESPONSE_OK:
        return file_path
    return None

