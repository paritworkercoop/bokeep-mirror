import sys

from bokeep.gui.gladesupport import GladeWindow

from gtk import ListStore

from decimal import Decimal

from os.path import abspath, dirname, join, exists

class trustor_entry(GladeWindow):
    def detach(self):
        self.widgets['vbox1'].reparent(self.top_window)

    def __init__(self, trust_trans, trans_id, trust_module, gui_parent, editable):

        self.gui_built = False
        self.editable = editable

        
        self.init()

        if not gui_parent == None:
            self.widgets['vbox1'].reparent(gui_parent)
        self.top_window.hide()
        self.gui_built = True


    def construct_filename(self, filename):
        import trustor_entry as trust_module
        return join( dirname( abspath( trust_module.__file__ ) ),
                              filename)
        
    def init(self):

        filename = 'mileage.glade'

        widget_list = [
            'window1',
            ]

        handlers = [
            'on_window_destroy',
            ]

        top_window = 'window1'
        GladeWindow.__init__(self, self.construct_filename(filename), top_window, widget_list, handlers)


