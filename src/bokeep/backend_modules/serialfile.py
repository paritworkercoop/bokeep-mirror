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
# bokeep imports
from module import BackendModule
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
            self.write_to_file( """transaction with identifier %(trans_id)s
%(description)s
chequenum %(chequenum)s
debits
%(debit_list)s
credits
%(credit_list)s

""" % { 'trans_id': self.count,
        'description': description,
        'chequenum': chequenum,
        'debit_list' : \
            '\n'.join(
                        str_repr_of_line(line)
                        for line in debits
                        ),
        'credit_list': \
            "\n".join( str_repr_of_line(line, True)
                       for line in credits )
        } )
        except IOError:
            raise BoKeepBackendException
                
        return_value = self.count
        self.count = self.count + 1
        return return_value

    def save(self):
        # nothing to do here, we always save after each write...
        pass

def get_module_class():
    return SerialFileModule
