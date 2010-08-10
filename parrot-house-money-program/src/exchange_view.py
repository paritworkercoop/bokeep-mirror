from trans_view import TransView

class ExchangeView(TransView):
    window_name = "exchange_view"

    def __init__(self, mainwindow, glade_file):
        TransView.__init__(self, mainwindow, glade_file)
        self.initialize_member_combo( self.debit_account_combo )

    def set_transaction(self, transaction):
        TransView.set_transaction(self, transaction)
        self.connect_debit_side_to_transaction()
        self.trans_amount.set_text( str( transaction.debit_amount ) )

    def connect_debit_side_to_transaction(self):
        if self.debit_account_combo.get_active() == -1:
            if self.transaction.debit_account == -1:
                self.transaction.debit_account = 0
            self.debit_account_combo.set_active(
                self.transaction.debit_account )
        elif self.transaction.debit_account == -1:
            self.transaction.debit_account = \
                self.debit_account_combo.get_active()

    def debit_account_changed(self, *args):
        self.transaction.debit_account = \
            self.debit_account_combo.get_active()

    def trans_amount_changed(self, *args):
        try :
            self.transaction.debit_amount.set( self.trans_amount.get_text() )
        except ValueError:
            self.NAN_icon.set_property("visible", True)
        else:
            self.NAN_icon.set_property("visible", False)
            
