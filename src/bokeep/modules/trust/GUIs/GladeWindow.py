#!/usr/bin/env python

#----------------------------------------------------------------------
# GladeWindow.py
# Dave Reed
# 12/15/2002
#----------------------------------------------------------------------

import os
import gtk
import gtk.glade
import traceback

#----------------------------------------------------------------------

def DoubleIteration(iter1, iter2):
    iter1 = iter(iter1)
    iter2 = iter(iter2)
    try:
        while True:
            yield iter1.next(), iter2.next()
    except StopIteration: pass
    

def search_file(filename, search_path):

    """Given a search path, find file
    """

    file_found = 0
    paths = search_path.split(os.pathsep)

    for path in paths:
        if os.path.exists(os.path.join(path, filename)):
            file_found = 1
            break

    if file_found:
        return os.path.abspath(os.path.join(path, filename))
    else:
        return None

#----------------------------------------------------------------------

class GladeWindow(object):

    '''A base class for displaying a GUI developed with Glade; create
    a subclass and add any callbacks and other code; the derived class
    __init__ method needs to call GladeWindow.__init__; callbacks that
    start with on_ are automatically connected'''

    #----------------------------------------------------------------------

    def set_search_path(cls, path):

        '''set the search path for looking for the .glade files'''

        cls.search_path = path

    set_search_path = classmethod(set_search_path)

    #----------------------------------------------------------------------

    def __init__(self, filename, top_window, widget_list, handlers,
                 pull_down_dict=None):

        '''
        __init__(self, filename, top_window, widget_list, pull_down_dict=None):

        filename: filename of the .glade file
        top_window: the glade name of the top level widget (this will then
           be accessible as self.top_window)
        widget_list: a list of glade names; the dictionary self.widgets
           will be created that maps these name to the actual widget object
        pull_down_dict: a dictionary that maps combo names to a tuple of
            strings to put in the combo
        '''
        
        self.widget_list = widget_list

        try:
            search_path = GladeWindow.search_path
        except:
            search_path = './'

        fname = search_file(filename, search_path)
        self.xml = gtk.glade.XML(fname)

        # connect callbacks
        self.cb_dict = {}
        for f in handlers:
            self.cb_dict[f] = getattr(self, f)
        self.xml.signal_autoconnect(self.cb_dict)

        self.widgets = {}
        for w in self.widget_list:
            self.widgets[w] = self.xml.get_widget(w)

        if pull_down_dict is not None:
            for w, l in pull_down_dict.items():
                self.widgets[w].set_popdown_strings(l)

        # set attribute for top_window so it can be accessed as self.top_window
        self.top_window = self.xml.get_widget(top_window)

        # window to show when this one is hidden
        self.prev_window = None

        # initialize callback func
        self.cb_func = None

    #----------------------------------------------------------------------

    def set_top_window(self, top_window):

        '''set_top_window(self, top_window):

        notebook pages that are in containers need to be able to change
        their top window, especially so the dialog is set_transient_for
        the actual main window
        '''
        
        self.top_window = top_window
        
    #----------------------------------------------------------------------


    def set_callback_function(self, cb_func, *cb_args, **cb_kwargs):

        '''set_callback_function(cb_func, *cb_args, **cb_kwargs):

        stores the cb_func and its cb_args and cb_kwargs
        '''
        self.cb_func = cb_func
        self.cb_args = cb_args
        self.cb_kwargs = cb_kwargs
        
    
    #----------------------------------------------------------------------

    def forward(self):
        self.next_window.show()
        self.top_window.hide()

    def back(self):
        self.hide()

    def show(self, center=1, prev_window=None, *args):

        '''show(self, center=1, prev_window=None, *args):

        display the top_window widget
        '''

        if prev_window is not None:
            self.prev_window = prev_window
        if center:
            self.top_window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        else:
            self.top_window.set_position(gtk.WIN_POS_NONE)
        self.top_window.show()

    #----------------------------------------------------------------------

    def hide(self):

        '''hide(self):

        hides the current window, shows self.prev_window
        if self.cb_func is not None, it is called with its cb_args
        and cb_kwargs
        '''

        self.top_window.hide()
        if self.prev_window is not None:
            self.prev_window.show()
        if self.cb_func is not None:
            self.cb_func(*self.cb_args, **self.cb_kwargs)
        if self.prev_window is None:
            gtk.main_quit()

    def on_forward_clicked(self, *args):
        if self.safe_to_move_forward():
            self.forward()

    def on_back_clicked(self, *args):
        self.back()

    def safe_to_move_forward(self):
        return True

    def add_widgets(self, *widgets):
        for name in widgets:
            self.widgets[name] = self.xml.get_widget(name)

    def on_window_destroy(*args):
        gtk.main_quit()

    def set_widget_state(self, widget, value):
        if isinstance(widget, gtk.Entry): 
            widget.set_text(value)
        if isinstance(widget, gtk.Calendar):
            widget.select_month(value[1], value[0])
            widget.select_day(value[2])
        if isinstance(widget, gtk.RadioButton):
            widget.set_active(value)
        if isinstance(widget, gtk.TreeView):
            tree_model = widget.get_model()
            for row in value:
                tree_model.append(row)

    def __setstate__(self, widget_values):
        if not self.__dict__.has_key('common_constructor_done'):
            self.common_constructor()
        for widget_name, widget_value in DoubleIteration(self.pickle_widget_names, widget_values):
            self.set_widget_state( self.widgets[widget_name], widget_value )
        self.init_completed = True

    def get_widget_state(self, widget):
        if isinstance(widget, gtk.Entry):
            return widget.get_text()
        if isinstance(widget, gtk.Calendar):
            (year, month, day) = widget.get_date()
            return [year, month, day]
        if isinstance(widget, gtk.RadioButton):
            if widget.get_active():
                return True
            else:
                return False
        if isinstance(widget, gtk.TreeView):
            tree_model = widget.get_model()
            existing_elements = []
            for row in tree_model:
                existing_elements.append(list(row))
            return existing_elements
        

    def __getstate__(self):
        return [ self.get_widget_state(self.widgets[widget_name])
                 for widget_name in self.pickle_widget_names ]
            
            
#----------------------------------------------------------------------
