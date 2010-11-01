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
from session_based_robust_backend_module import SessionBasedRobustBackendModule
from bokeep.util import attribute_or_blank
from decimal import Decimal 

ZERO = Decimal(0)

class SerialFileModule(SessionBasedRobustBackendModule):
    def __init__(self):
        SessionBasedRobustBackendModule.__init__(self)
        self.count = 0
        self.accounting_file = "AccountingFile.txt"

    def open_session(self):
        try:
            return open(self.accounting_file, 'a')
        except IOError:
            return None

    def write_to_file(self, msg):
        try:
            self._v_session_active.write(msg)
        except IOError, e:
             raise BoKeepBackendException(e.message)

    def remove_backend_transaction(self, backend_ident):
        assert( backend_ident < self.count )
        self.write_to_file("remove transaction with identifier %s\n\n" % 
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
                      
        return_value = self.count
        self.count += 1
        return return_value

    def close(self):
        try:
            self._v_session_active.close()
        except IOError:
            # probably nothing to do here, super class close() will del
            # self._v_session_active
            pass
        SessionBasedRobustBackendModule.close(self)

    def save(self):
        self.close()
        self.open_session_and_retain()

def get_module_class():
    return SerialFileModule
