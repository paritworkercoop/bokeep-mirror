import sys

from GladeWindow import GladeWindow

from gtk import ListStore

from decimal import Decimal

from os.path import abspath, dirname, join, exists

class trustor_entry(GladeWindow):
    def detach(self):
        self.widgets['vbox1'].reparent(self.top_window)

    def __init__(self, trust_trans, trans_id, trust_module, gui_parent, editable):

        self.gui_built = False
        self.editable = editable

        ''' '''
        
        self.init()
        self.extended_init()

        if not gui_parent == None:
            self.widgets['vbox1'].reparent(gui_parent)
        self.top_window.hide()
        self.gui_built = True



    #----------------------------------------------------------------------

    def extended_init(self):
        self.add_widgets('trustor_combo', 'vbox1')
        self.trustor_combo = self.widgets['trustor_combo']
        self.trustor_list = ListStore( str )
        self.trustor_combo.set_model(self.trustor_list)
        index = 0
        use_index = -1
        for trustor in self.trustors:
            self.trustor_list.append([trustor])
            if not(self.trans_trustor == None) and self.trans_trustor.name == trustor:
                use_index = index
            index += 1
 
        if use_index > -1:
            self.trustor_combo.set_active(use_index)
            self.widgets['amount_entry'].set_text(str(self.trust_trans.get_transfer_amount()))
        else:
            self.trustor_combo.set_active(0)

        if not self.editable:
            self.widgets['amount_entry'].set_sensitive(False)


    def construct_filename(self, filename):
        import trustor_entry as trust_module
        return join( dirname( abspath( trust_module.__file__ ) ),
                              filename)
        
    def init(self):

        filename = 'data/trustor_entry.glade'

        widget_list = [
            'window1',
            'amount_entry',
            ]

        handlers = [
            'on_window_destroy',
            'on_trustor_combo_changed',
            'on_amount_entry_changed',
            ]

        top_window = 'window1'
        GladeWindow.__init__(self, self.construct_filename(filename), top_window, widget_list, handlers)


    def update_trans(self):
        entered_amount = self.widgets['amount_entry'].get_text()

        if entered_amount == '':
            print 'setting amount to zero'
            self.trust_trans.transfer_amount = Decimal('0')
        else:
            print 'using ' + entered_amount + ' for amount'
            self.trust_trans.transfer_amount = Decimal(entered_amount)

        print self.trust_trans.get_transfer_amount()
        trustor = self.trust_module.get_trustor(self.widgets['trustor_combo'].get_active_text())
        self.trust_module.associate_transaction_with_trustor(self.trans_id, self.trust_trans, trustor.name)

    def on_window_destroy(self, *args):
        if self.editable:
            self.update_trans()
        GladeWindow.on_window_destroy(self, *args)
    #----------------------------------------------------------------------

    def on_trustor_combo_changed(self, *args):
        if self.gui_built:
            self.update_trans()

    #----------------------------------------------------------------------

    def on_amount_entry_changed(self, *args): 
        if self.gui_built:
            self.update_trans()