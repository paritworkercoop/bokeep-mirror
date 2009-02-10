# bokeep imports
from module import BackendModule
from bokeep.book_transaction import \
    BoKeepTransactionNotMappableToFinancialTransaction
from bokeep.util import attribute_or_blank
from decimal import Decimal 

ZERO = Decimal(0)

class SerialFileModule(BackendModule):
    def __init__(self):
        BackendModule.__init__(self)
        self.count = 0
        self.accounting_file = "AccountingFile.txt"

    def write_to_file(self, msg):
        f = open(self.accounting_file, 'a')
        f.write(msg)
        f.close()

    def can_write(self):
        try:
            f = open(self.accounting_file, 'a')
            f.close()
        except IOError:
            return False
        else:
            return True

    def remove_backend_transaction(self, backend_ident):
        assert( backend_ident < self.count )
        self.write_to_file("remove transaction with identifier %s\n\n" % \
                               backend_ident )
        
    def create_backend_transaction(self, fin_trans):
        description = attribute_or_blank(fin_trans, "description")
        chequenum = attribute_or_blank(fin_trans, "chequenum")
        debits = []
        credits = []
        for trans_line in fin_trans.lines:
            if trans_line.amount >= ZERO:
                debits.append(trans_line)
            else:
                credits.append(trans_line)

        def str_repr_of_line(line, reverse=False):
            amount = line.amount
            if reverse:
                amount = -amount
            return "%s %s" % (amount,
                                attribute_or_blank(line, 'comment') )

        try:
            self.write_to_file( """%(description)s
chequenum %(chequenum)s
debits
%(debit_list)s
credits
%(credit_list)s

""" % \
                               { 'description': description,
                                 'chequenum': chequenum,
                                 'debit_list' : '\n'.join(
                        str_repr_of_line(line)
                        for line in debits
                        ),
                                 'credit_list': '\n'.join(
                        str_repr_of_line(line, True)
                        for line in credits
                        ),
                                   } )
        except IOError:
            raise BoKeepTransactionNotMappableToFinancialTransaction()
                
        self.count = self.count + 1
        return self.count

    def save(self):
        # nothing to do here, we always save after each write...
        pass

def get_module_class():
    return SerialFileModule
