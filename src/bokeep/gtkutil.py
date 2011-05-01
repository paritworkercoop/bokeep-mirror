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

# python imports
from datetime import date

# gtk imports
from gtk import \
    FileChooserDialog, MessageDialog, \
    FILE_CHOOSER_ACTION_SAVE, FILE_CHOOSER_ACTION_OPEN, \
    STOCK_CANCEL, RESPONSE_CANCEL, \
    STOCK_SAVE, RESPONSE_OK, STOCK_OPEN, DIALOG_MODAL, \
    MESSAGE_ERROR, BUTTONS_OK, \
    TreeView, ListStore, STOCK_ADD, STOCK_DELETE, VBox, HBox, Label, Button

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

def get_current_date_of_gtkcal(cal):
    (year, month, day) = cal.get_date()
    return date(year, month+1, day)

def gtk_error_message(msg, parent=None):
    error_dialog = MessageDialog(parent, DIALOG_MODAL, 
                                 MESSAGE_ERROR, BUTTONS_OK, msg)
    error_dialog.run()
    error_dialog.destroy()

def start_stock_button(stock_code):
    but = Button()
    but.set_property('use-stock', True)
    but.set_label(stock_code)
    return but

def pack_in_stock_but_and_ret(but, box):
    box.pack_start(but, expand=False)
    return but

def fieldtype_transform(fieldtype):
    if fieldtype == date:
        return str
    return fieldtype

def create_editable_type_defined_listview_and_model(field_list):
    vbox = VBox()
    vbox.pack_start(Label("hello"), expand=False)
    tv = TreeView()
    model = ListStore( *tuple(fieldtype_transform(fieldtype)
                              for fieldname, fieldtype in field_list)  )
    vbox.pack_start(tv)
    tv.model = model
    hbox = HBox()
    buttons = [ pack_in_stock_but_and_ret(start_stock_button(code), hbox)
                for code in (STOCK_ADD, STOCK_DELETE) ]
    vbox.pack_start(hbox, expand=False)
    return model, tv, vbox
