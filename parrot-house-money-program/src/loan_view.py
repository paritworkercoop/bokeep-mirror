from exchange_view import ExchangeView

class LoanView(ExchangeView):
    window_name = "loan_view"

    def __init__(self, mainwindow, glade_file):
        ExchangeView.__init__(self, mainwindow, glade_file)

    def set_transaction(self, transaction):
        ExchangeView.set_transaction(self, transaction)
        self.trans_description.set_text( transaction.description )

    def trans_description_changed(self, *args):
        self.transaction.description = self.trans_description.get_text()
