from bokeep.book_transaction import Transaction

class Type1Transaction(Transaction):
    def __init__(self):
        Transaction.__init__(self)
        self.reset_data()
    
    def reset_data(self):
        self.data = "blah"

    def append_data(self, append_text):
        self.data += append_text
