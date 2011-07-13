# Copyright (C) 2010-2011  ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
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
# Author: Samuel Pauls <samuel@parit.ca>

# python imports
from datetime import date, timedelta
import datetime
from itertools import islice, chain, izip
from decimal import InvalidOperation, Decimal

# gtk imports
from gtk import \
    FileChooserDialog, MessageDialog, \
    FILE_CHOOSER_ACTION_SAVE, FILE_CHOOSER_ACTION_OPEN, \
    FILE_CHOOSER_ACTION_SELECT_FOLDER, \
    STOCK_CANCEL, RESPONSE_CANCEL, \
    STOCK_SAVE, RESPONSE_OK, STOCK_OPEN, DIALOG_MODAL, \
    MESSAGE_ERROR, BUTTONS_OK, \
    TreeView, ListStore, STOCK_ADD, STOCK_DELETE, VBox, HBox, Label, Button, \
    TreeViewColumn, CellRendererText, main as gtk_main, Window, main_quit, \
    CellRendererCombo, CellRendererText, Dialog, Calendar, Entry
import gobject
import gtk

# zodb imports
from persistent.list import PersistentList

# bokeep imports
from bokeep.util import null_function

COMBO_NO_SELECTION = -1

def file_selection_path(msg="choose file",
                        selection_code=FILE_CHOOSER_ACTION_OPEN):
    fcd = FileChooserDialog(
        msg,
        None,
        selection_code,
        (STOCK_CANCEL, RESPONSE_CANCEL, STOCK_OPEN, RESPONSE_OK) )
    fcd.set_modal(True)
    result = fcd.run()
    file_path = fcd.get_filename()
    fcd.destroy()
    if result == RESPONSE_OK:
        return file_path
    return None

def input_entry_dialog(msg, default_answer="", parent=None):
    dia = Dialog(
        msg, parent, gtk.DIALOG_MODAL |gtk.DIALOG_DESTROY_WITH_PARENT,
        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                 gtk.STOCK_OK, RESPONSE_OK) )
    dia.vbox.pack_start(Label(msg))
    da_entry = Entry()
    dia.vbox.pack_end( da_entry )
    dia.show_all()
    result = dia.run()
    dia.destroy()
    return None if result != RESPONSE_OK else da_entry.get_text()

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


class CellRendererFile(CellRendererText):
    def __init__(self, file_chooser_type=FILE_CHOOSER_ACTION_OPEN):
        gtk.CellRendererText.__init__(self)
        self.file_chooser_type = file_chooser_type

    def do_start_editing(self, event, widget, path, background_area,
                         cell_area, flags):
        new_file_path = file_selection_path(
            "Select a file" 
            if self.file_chooser_type == FILE_CHOOSER_ACTION_OPEN 
            else "Select a directory",

            self.file_chooser_type)
        if new_file_path != None:
            self.emit('edited', path, new_file_path)

gobject.type_register(CellRendererFile)


# CellRendererDate code was copied and modified from the pygtk FAQ
# by Mark Jenkins <mark@parit.ca> on May 5, 2011
#
# http://faq.pygtk.org/index.py?req=index
# http://faq.pygtk.org/index.py?req=show&file=faq13.056.htp
#
# Presumably this is under the same license as the pygtk code and other
# documentation
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Library General Public
#    License as published by the Free Software Foundation; either
#    version 2 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Library General Public License for more details.
#

CELL_RENDERER_DATE_FORMAT = '%d/%m/%Y'

def cell_renderer_date_to_string(a_date, date_format=CELL_RENDERER_DATE_FORMAT):
    return a_date.strftime(date_format)

def cell_renderer_string_to_date(
    a_date_str, date_format=CELL_RENDERER_DATE_FORMAT):
    new_date = datetime.datetime.strptime(a_date_str, date_format)
    return date(new_date.year, new_date.month, new_date.day)

class CellRendererDate(gtk.CellRendererText):

    __gtype_name__ = 'CellRendererDate'

    def __init__(self):
        gtk.CellRendererText.__init__(self)
        self.calendar_window = None
        self.calendar = None

    def _create_calendar(self, treeview):
        self.calendar_window = gtk.Dialog(parent=treeview.get_toplevel())
        self.calendar_window.action_area.hide()
        self.calendar_window.set_decorated(False)
        self.calendar_window.set_property('skip-taskbar-hint', True)
        
        self.calendar = gtk.Calendar()
        self.calendar.display_options(gtk.CALENDAR_SHOW_DAY_NAMES | gtk.CALENDAR_SHOW_HEADING)
        self.calendar.connect('day-selected-double-click', self._day_selected, None)
        self.calendar.connect('key-press-event', self._day_selected)
        self.calendar.connect('focus-out-event', self._selection_cancelled)
        self.calendar_window.set_transient_for(None) # cancel the modality of dialog
        self.calendar_window.vbox.pack_start(self.calendar)
        
        # necessary for getting the (width, height) of calendar_window
        self.calendar.show()
        self.calendar_window.realize()

    def do_start_editing(self, event, treeview, path, background_area, cell_area, flags):
        if not self.get_property('editable'):
            return

        if not self.calendar_window:
            self._create_calendar(treeview)

        # select cell's previously stored date if any exists - or today
        if self.get_property('text'):
            date = cell_renderer_string_to_date(self.get_property('text') )
        else:
            date = datetime.datetime.today()
        self.calendar.freeze() # prevent flicker
        (year, month, day) = (date.year, date.month - 1, date.day) # datetime's month starts from one
        self.calendar.select_month(int(month), int(year))
        self.calendar.select_day(int(day))
        self.calendar.thaw()

        # position the popup below the edited cell (and try hard to keep the popup within the toplevel window)
        (tree_x, tree_y) = treeview.get_bin_window().get_origin()
        (tree_w, tree_h) = treeview.window.get_geometry()[2:4]
        (calendar_w, calendar_h) = self.calendar_window.window.get_geometry()[2:4]
        x = tree_x + min(cell_area.x, tree_w - calendar_w + treeview.get_visible_rect().x)
        y = tree_y + min(cell_area.y, tree_h - calendar_h + treeview.get_visible_rect().y)
        self.calendar_window.move(x, y)

        response = self.calendar_window.run()
        if response == gtk.RESPONSE_OK:
            (year, month, day) = self.calendar.get_date()
            date = cell_renderer_date_to_string(datetime.date(year, month + 1, day)) # gtk.Calendar's month starts from zero
            self.emit('edited', path, date)
            self.calendar_window.hide()
        return None # don't return any editable, our gtk.Dialog did the work already

    def _day_selected(self, calendar, event):
        # event == None for day selected via doubleclick
        if not event or event.type == gtk.gdk.KEY_PRESS and gtk.gdk.keyval_name(event.keyval) == 'Return':
            self.calendar_window.response(gtk.RESPONSE_OK)
            # should this perhaps be indented over
            return True

    def _selection_cancelled(self, calendar, event):
        self.calendar_window.response(gtk.RESPONSE_CANCEL)
        return True

gobject.type_register(CellRendererDate)

# End CellRendererDate code pulled from PyGTK FAQ

COMBO_TYPE_HAS_ENTRY_FIELD, COMBO_TYPE_STORE_TYPE_FIELD, \
    COMBO_TYPE_FIRST_VALUE = range(3)

FIELD_NAME, FIELD_TYPE = range(2)

def listvalue_from_string_to_original_type(value, field_type):
    if field_type == date:
        return cell_renderer_string_to_date(value)
    elif type(field_type) == tuple:
        # for combo lists without an arbitrary entry field, this
        # conversion should never take place, the original value
        # should be used
        assert(field_type[COMBO_TYPE_HAS_ENTRY_FIELD])

        # woot, recursive answer
        return listvalue_from_string_to_original_type(
            value, field_type[COMBO_TYPE_STORE_TYPE_FIELD] )
    elif type(field_type) == dict and field_type['type'] == file:
        return value
    # possible exception here caught by caller
    return field_type(value)

def combobox_list_strings_and_values_iteration(field_type):
    sliced_values_iter = slice_the_values_part_of_a_combo_tuple(field_type)
    if type(field_type[COMBO_TYPE_STORE_TYPE_FIELD]) == tuple:
        return izip(
            sliced_values_iter,
            field_type[COMBO_TYPE_STORE_TYPE_FIELD],
            )
    else:
        return ( (listvalue_to_string_from_original_type(
                    combo_value, field_type), combo_value)
                 for combo_value in sliced_values_iter )

def listvalue_to_string_from_original_type(value, field_type):
    if field_type == date:
        return cell_renderer_date_to_string(value)
    elif type(field_type) == tuple:
        multi_chooser_assertion(field_type)
        # if the user can explicitly define a value, or
        # they are values of convertible types and not a specific list
        # of value, then we do the conversion recursively (woot!)
        if (field_type[COMBO_TYPE_HAS_ENTRY_FIELD] or 
            type(field_type[COMBO_TYPE_STORE_TYPE_FIELD]) != tuple ):
            return listvalue_to_string_from_original_type(
            value, field_type[COMBO_TYPE_STORE_TYPE_FIELD] )
        # else we have an arbitrary list of values to convert from
        else:
            assert( type(field_type[COMBO_TYPE_STORE_TYPE_FIELD]) == tuple )
            # linear search time baby!
            for possible_string, possible_value in \
                    combobox_list_strings_and_values_iteration(field_type):
                if value == possible_value:
                    return possible_string
            else:
                # we should never reach the end of this loop, something should
                # match
                assert(False)
    else:
        return str(value)

def set_underlying_model_pair(
     model_row_path, new_str, new_real_value, original_model, original_column):
    original_model.set_value(
        original_model.get_iter(model_row_path), original_column,
        new_str )
    location_of_real_value_in_model = \
        len(original_model[model_row_path])/2 + original_column
    original_model.set_value(
        original_model.get_iter(model_row_path),
        location_of_real_value_in_model,
        new_real_value )

def cell_edited_update_original_modelhandler(
    cellrenderer, model_row_path, new_str, original_model, original_column,
    field_type):
    try:
        new_real_value = listvalue_from_string_to_original_type(
            new_str, field_type )
    # do nothing if conversion to int fails
    except ValueError: pass
    # do nothing if conversion to Decimal fails
    except InvalidOperation: pass
    # else we use the converted value
    else:
        set_underlying_model_pair(model_row_path, new_str, new_real_value,
                                  original_model, original_column )

def combo_cell_edited_update_original_modelhandler(
    cellrenderer, model_row_path, new_str, original_model, original_column,
    lookup_dict):
    if new_str in lookup_dict:
        set_underlying_model_pair(model_row_path, new_str, lookup_dict[new_str],
                                  original_model, original_column)           

def editable_listview_add_button_clicked_handler(button, model, new_row_func,
                                                 field_list):
    """new_row_func: This function is called and its return value is used to
       populate the new row.  If "None" is returned, the new row isn't added."""
    addition = new_row_func()
    if addition != None:
        new_row = list(addition)
        model.append( tuple(
            chain( (listvalue_to_string_from_original_type(
                        item, field_list[i][FIELD_TYPE])
                    for i, item in enumerate(new_row)),
                   new_row ) # chain
            ) ) # tuple and append

def editable_listview_del_button_clicked_handler(button, tv):
    model, treeiter = tv.get_selection().get_selected()
    if treeiter != None:
        model.remove(treeiter)

def slice_the_data_part_of_a_row(row):
    return islice(row, len(row)/2, None)

def slice_the_values_part_of_a_combo_tuple(combo_type_tuple):
    return islice(combo_type_tuple, COMBO_TYPE_FIRST_VALUE, None)

def row_changed_handler(
    model, path, treeiter, parralell_list, change_register, field_list,
    changed_pre_hook, changed_post_hook):
    new_row_iter = tuple(slice_the_data_part_of_a_row(model[path[0]]))
    row_list = parralell_list[ path[0] ]
    changed_pre_hook(path[0], row_list, new_row_iter)
    # we change the row in place, item by item
    for i, value in enumerate(new_row_iter):
        # expand the list if needed
        if i == len(row_list):
            row_list.append(value)
        else:
            row_list[i] = value
    # shrink the list if the new one is smaller
    last_elem = len(row_list) - 1
    while last_elem > i:
        row_list.pop(i)
        last_elem-=1            
    changed_post_hook(path[0], row_list, new_row_iter)
    change_register()

def row_inserted_handler(
    model, path, treeiter, parralell_list, change_register,
    insert_pre_hook, insert_post_hook):
    new_row = PersistentList(slice_the_data_part_of_a_row(model[path[0]]))
    insert_pre_hook(path[0], new_row)
    parralell_list.insert(path[0],
                          new_row,
                          ) # insert
    insert_post_hook(path[0], new_row)
    change_register()

def row_deleted_handler(
    model, path, parralell_list, change_register,
    del_pre_hook, del_post_hook):
    del_pre_hook(path[0], parralell_list[ path[0] ])
    del parralell_list[ path[0] ]
    del_post_hook(path[0])
    change_register()

def multi_chooser_assertion(fieldtype):
    # if there is a specific list of stored values, we had better
    # not be able to enter an arbitrary value
    #
    # stated with different logic, we expect to be not allowed arbitary
    # to not be provided a specific object list
    assert( not fieldtype[COMBO_TYPE_HAS_ENTRY_FIELD] or
            type(fieldtype[COMBO_TYPE_STORE_TYPE_FIELD]) != tuple )

def display_fieldtype_transform(fieldtype):
    # will differ once we have support for things other than CellRendererText
    # and derivitives of it
    #
    # other functions will need to change as well, such as
    # transform_list_row_into_twice_repeated_row_for_model
    # and editable_listview_add_button_clicked_handler
    return str

def store_fieldtype_transform(fieldtype):
    if fieldtype in(date, Decimal):
        return gobject.TYPE_PYOBJECT
    # ComboBox or EntryComboBox selection when the type is a tuple
    elif type(fieldtype) == tuple:
        multi_chooser_assertion(fieldtype)

        # if we're dealing with some kind of type that can be eddited
        # such as str, int, Decimal and Date
        if fieldtype[COMBO_TYPE_HAS_ENTRY_FIELD]:
            # woot, recursion, fixes the case where we have a list of
            # date or Decimal compared to just returning
            # fieldtype[COMBO_TYPE_STORE_TYPE_FIELD]
            return store_fieldtype_transform(
                fieldtype[COMBO_TYPE_STORE_TYPE_FIELD])
        # else we're not able to enter an arbitrary value, then we just store
        # whatever original py object co-responds to the list entry
        else:
            return gobject.TYPE_PYOBJECT
    elif type(fieldtype) == dict and fieldtype['type'] == file:
        return str
    return fieldtype

def transform_list_row_into_twice_repeated_row_for_model(list_row, field_list):
    return chain( (listvalue_to_string_from_original_type(
                item, field_list[i][FIELD_TYPE])
                   for i, item in enumerate(list_row)),
                  list_row )

def create_editable_type_defined_listview_and_model(
    field_list, new_row_func, parralell_list, change_register,
    readonly=False,
    insert_pre_hook=null_function, insert_post_hook=null_function,
    change_pre_hook=null_function, change_post_hook=null_function,
    del_pre_hook=null_function, del_post_hook=null_function):
    vbox = VBox()
    tv = TreeView()
    model = ListStore( * chain((display_fieldtype_transform(fieldtype)
                                for fieldname, fieldtype in field_list),
                               (store_fieldtype_transform(fieldtype)
                                for fieldname, fieldtype in field_list)
                               ) # chain
                         ) # ListStore
    # it is important to do this fill of the liststore
    # with the existing items first prior to adding event handlers
    # (row-changed, row-inserted, row-deleted) that
    # look for changes and keep the two lists in sync
    for list_row in parralell_list:
        model.append(
            tuple(transform_list_row_into_twice_repeated_row_for_model(
                    list_row, field_list) )
            ) # append
    if not readonly:
        model.connect("row-changed",
                      row_changed_handler,
                      parralell_list, change_register, field_list,
                      change_pre_hook, change_post_hook,
                      )
        model.connect("row-inserted",
                      row_inserted_handler,
                      parralell_list, change_register,
                      insert_pre_hook, insert_post_hook )
        model.connect("row-deleted",
                      row_deleted_handler, parralell_list, change_register,
                      del_pre_hook, del_post_hook)

    for i, (fieldname, fieldtype) in enumerate(field_list):
        def setup_edited_handler_for_renderer_to_original_model(cell_renderer):
            cell_renderer.connect(
                'edited',
                cell_edited_update_original_modelhandler, model, i,
                field_list[i][FIELD_TYPE])
            return cell_renderer

        if fieldtype == date:
            cell_renderer = \
                setup_edited_handler_for_renderer_to_original_model(
                CellRendererDate() )
        elif type(fieldtype) == tuple:
            cell_renderer = CellRendererCombo()
            cell_renderer.set_property("has-entry",
                                       fieldtype[COMBO_TYPE_HAS_ENTRY_FIELD])
            combo_liststore = ListStore(
                str, store_fieldtype_transform(fieldtype) )
            for combo_string, combo_value in \
                    combobox_list_strings_and_values_iteration(fieldtype):
                combo_liststore.append( (combo_string, combo_value) )
            cell_renderer.set_property("model", combo_liststore)
            cell_renderer.set_property("text-column", 0)
            if fieldtype[COMBO_TYPE_HAS_ENTRY_FIELD]:
                setup_edited_handler_for_renderer_to_original_model(
                    cell_renderer)
            else:
                lookup_dict = dict(
                    combobox_list_strings_and_values_iteration(fieldtype) )
                cell_renderer.connect(
                'edited',
                combo_cell_edited_update_original_modelhandler, model, i,
                lookup_dict)

        elif type(fieldtype) == dict and fieldtype['type'] == file:
            cell_renderer = CellRendererFile(
                fieldtype['file_type']  if 'file_type' in fieldtype
                else FILE_CHOOSER_ACTION_OPEN 
                )
            setup_edited_handler_for_renderer_to_original_model(cell_renderer)
        else:
            cell_renderer = \
                setup_edited_handler_for_renderer_to_original_model(
                CellRendererText() )
        if not readonly:
            cell_renderer.set_property("editable", True)
            cell_renderer.set_property("editable-set", True)
        tvc = TreeViewColumn(fieldname, cell_renderer, text=i)
        tv.append_column(tvc)
    vbox.pack_start(tv)
    tv.set_model(model)
    hbox = HBox()
    buttons = [ pack_in_stock_but_and_ret(start_stock_button(code), hbox)
                for code in (STOCK_ADD, STOCK_DELETE) ]
    if readonly: 
        for button in buttons:
            button.set_property("sensitive", False)
    else:
        buttons[0].connect(
            "clicked",
            editable_listview_add_button_clicked_handler,
            model, new_row_func, field_list  )
        buttons[1].connect(
            "clicked",
            editable_listview_del_button_clicked_handler,
            tv )
    vbox.pack_start(hbox, expand=False)
    return model, tv, vbox

class TestProgType(object):
    pass

def test_program_return_new_row():
    return (date.today(), 'yep', 'me', 2, 'aha', 2, '/', date.today(),
            None,
            Decimal('5.34') )

def test_prog_list_changed(*args):
    print 'list changed'

def main():
    print 'answer', input_entry_dialog("who what?")

    w = Window()
    w.resize(200, 200)
    w.connect( "delete-event", main_quit )
    vbox = VBox()
    w.add(vbox)
    ONE_DAY = timedelta(days=1)
    existing_list = [PersistentList(test_program_return_new_row())]
    model, tv, tv_vbox = \
        create_editable_type_defined_listview_and_model(
        ( ('date', date,),
          ('choose-me',
           (True, str, 'yo', 'hi', 'me', 'fun')
           ), # end choose-me tuple
          ('choose-me-only',
           (False, str, 'yo', 'hi', 'me', 'fun')
           ), # end choose-me-only tuple
          ('choose-me-num',
           (False, int, 1, 2, 3, 4)
           ), # end choose-num tuple
          ('description', str),
          ('count', int),
          ('file_path', {'type': file,
                         'file_type':FILE_CHOOSER_ACTION_SELECT_FOLDER} ),
          ('choose-me-date',
           (False, date,
            date.today() - ONE_DAY, date.today(), date.today() + ONE_DAY ) ),
          ('choose-me-obj',
           (False, (None, TestProgType(), TestProgType()),
            'None', 'obj 1', 'obj 2' ) ),
          ('choose-me-Decimal',
           (True, Decimal, '3.1', '3.4') ),
          ), # end type tuple
        test_program_return_new_row, existing_list, test_prog_list_changed,
        False
        ) # create_editable_type_defined_listview_and_model
    vbox.pack_start( tv_vbox )
    w.show_all()
    gtk_main()

if __name__ == "__main__":
    main()
