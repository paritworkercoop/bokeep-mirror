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
import datetime
from itertools import islice

# gtk imports
from gtk import \
    FileChooserDialog, MessageDialog, \
    FILE_CHOOSER_ACTION_SAVE, FILE_CHOOSER_ACTION_OPEN, \
    STOCK_CANCEL, RESPONSE_CANCEL, \
    STOCK_SAVE, RESPONSE_OK, STOCK_OPEN, DIALOG_MODAL, \
    MESSAGE_ERROR, BUTTONS_OK, \
    TreeView, ListStore, STOCK_ADD, STOCK_DELETE, VBox, HBox, Label, Button, \
    TreeViewColumn, CellRendererText, main as gtk_main, Window, main_quit, \
    CellRendererCombo, CellRendererText, Dialog, Calendar
import gobject
import gtk

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

def iterative_append_to_liststore(liststore, itersource):
    for value in itersource:
        liststore.append(value)

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
    return datetime.datetime.strptime(a_date_str, date_format)    

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

COMBO_TYPE_HAS_ENTRY_FIELD, COMBO_TYPE_STORE_TYPE_FIELD, \
    COMBO_TYPE_FIRST_VALUE = range(3)

def fieldtype_transform(fieldtype):
    if fieldtype == date:
        return str
    elif type(fieldtype) == tuple:
        return fieldtype[COMBO_TYPE_STORE_TYPE_FIELD]
    return fieldtype

def cell_edited_update_original_modelhandler(
    cellrenderer, model_row_path, new_str, original_model, original_column):
    original_model.set_value(
        original_model.get_iter(model_row_path), original_column,
        new_str )

def editable_listview_add_button_clicked_handler(button, model, new_row_func):
    model.append( new_row_func() )

def editable_listview_del_button_clicked_handler(button, tv):
    model, treeiter = tv.get_selection().get_selected()
    if treeiter != None:
        model.remove(treeiter)

def row_changed_handler(
    model, path, treeiter, parralell_list, change_register):
    parralell_list[ path[0] ] = tuple(model[path[0]])
    change_register()

def row_inserted_handler(
    model, path, treeiter, new_empty_row, parralell_list, change_register):
    parralell_list.insert(path[0], new_empty_row )
    change_register()

def row_deleted_handler(
    model, path, parralell_list, change_register):
    del parralell_list[ path[0] ]
    change_register()

def create_editable_type_defined_listview_and_model(
    field_list, new_empty_row, new_row_func, parralell_list, change_register):
    vbox = VBox()
    tv = TreeView()
    model = ListStore( *tuple(fieldtype_transform(fieldtype)
                              for fieldname, fieldtype in field_list)  )
    model.connect("row-changed",
                  row_changed_handler,
                  parralell_list, change_register )
    model.connect("row-inserted",
                  row_inserted_handler, new_empty_row,
                  parralell_list, change_register )
    model.connect("row-deleted",
                  row_deleted_handler, parralell_list, change_register )
    for i, (fieldname, fieldtype) in enumerate(field_list):
        if fieldtype == date:
            cell_renderer = CellRendererDate()
        elif type(fieldtype) == tuple:
            cell_renderer = CellRendererCombo()
            cell_renderer.set_property("has-entry",
                                       fieldtype[COMBO_TYPE_HAS_ENTRY_FIELD])
            combo_liststore = ListStore(
                str, fieldtype[COMBO_TYPE_STORE_TYPE_FIELD] )
            iterative_append_to_liststore(
                combo_liststore,
                ( (str(combo_value), combo_value)
                  for combo_value in islice(
                        fieldtype, COMBO_TYPE_FIRST_VALUE, None) ) )
            cell_renderer.set_property("model", combo_liststore)
            cell_renderer.set_property("text-column", 0)
        else:
            cell_renderer = CellRendererText()
        cell_renderer.connect(
            'edited',
            cell_edited_update_original_modelhandler, model, i)
        cell_renderer.set_property("editable", True)
        cell_renderer.set_property("editable-set", True)
        tvc = TreeViewColumn(fieldname, cell_renderer, text=i)
        tv.append_column(tvc)
    vbox.pack_start(tv)
    tv.set_model(model)
    hbox = HBox()
    buttons = [ pack_in_stock_but_and_ret(start_stock_button(code), hbox)
                for code in (STOCK_ADD, STOCK_DELETE) ]
    buttons[0].connect(
        "clicked",
        editable_listview_add_button_clicked_handler,
        model, new_row_func )
    buttons[1].connect(
        "clicked",
        editable_listview_del_button_clicked_handler,
        tv )
    vbox.pack_start(hbox, expand=False)
    return model, tv, vbox

def test_program_return_new_row():
    return (cell_renderer_date_to_string(date.today()), 'yep', 'aha')

def test_prog_list_changed(*args):
    print 'list changed'

def main():
    w = Window()
    w.resize(200, 200)
    w.connect( "delete-event", main_quit )
    vbox = VBox()
    w.add(vbox)
    model, tv, tv_vbox = \
        create_editable_type_defined_listview_and_model(
        ( ('date', date,),
          ('choose-me',
           (True, str, 'yo', 'hi', 'me', 'fun')
           ), # end choose-me tuple
          ('description', str),
          ), # end type tuple
        ('', '', ''),
        test_program_return_new_row, [], test_prog_list_changed,
        ) # create_editable_type_defined_listview_and_model
    vbox.pack_start( tv_vbox )
    w.show_all()
    gtk_main()

if __name__ == "__main__":
    main()
