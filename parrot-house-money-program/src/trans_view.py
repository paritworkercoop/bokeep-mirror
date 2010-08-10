# gtk imports
from gtk import ListStore

# import from this project
from members import member_list, MEMBER_NAME
from glade_util import load_glade_file_get_widgets_and_connect_signals

class TransView(object):
    def __init__(self, mainwindow, glade_file):
        self.mainwindow = mainwindow
        
        load_glade_file_get_widgets_and_connect_signals(
            glade_file, self.window_name, self, self )

        self.member_list_model = ListStore(str)
        for member in member_list:
            self.member_list_model.append( (member[MEMBER_NAME],) )
        
        self.initialize_member_combo( self.credit_account_combo )

    def initialize_member_combo(self, combo):
        combo.child.set_editable(False)

        combo.set_model( self.member_list_model )
        
        # Make the combo use the 0th column in the above model if
        # it isn't using a column already.
        # Wierdly, this isn't needed on all the combos, the credit
        # on in shopping view is already set to 0
        if combo.get_text_column() == -1:
            combo.set_text_column(0)

    def send_to_main(self):
        self.view_vbox.reparent( self.mainwindow.main_vbox )

    def remove_from_main(self):
        self.view_vbox.reparent( getattr( self, self.window_name) )

    def connect_credit_side_to_transaction(self):
        if self.credit_account_combo.get_active() == -1:
            if self.transaction.credit_account == -1:
                self.transaction.credit_account = 0
            self.credit_account_combo.set_active(
                self.transaction.credit_account )
        elif self.transaction.credit_account == -1:
            self.transaction.credit_account = \
                self.credit_account_combo.get_active()
    
    def set_transaction(self, transaction):
        self.transaction = transaction
        self.connect_credit_side_to_transaction()

    def credit_account_changed(self, *args):
        self.transaction.credit_account = \
            self.credit_account_combo.get_active()
