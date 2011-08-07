# Copyright (C) 2010-2011  ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
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
# Authors: Mark Jenkins <mark@parit.ca>
#          Samuel Pauls <samuel@parit.ca>

# bokeep imports
from plugin import \
    BoKeepBackendException, BoKeepBackendResetException
from session_based_robust_backend_plugin import SessionBasedRobustBackendPlugin
from bokeep.util import attribute_or_blank
from bokeep.backend_plugins.serialfile_backend_config import \
    SerialFileConfigDialog
from decimal import Decimal 
from sys import stderr

# gtk imports
from gtk import \
    RESPONSE_OK, RESPONSE_CANCEL, \
    FILE_CHOOSER_ACTION_SAVE, FileChooserDialog, \
    STOCK_CANCEL, STOCK_SAVE

ZERO = Decimal(0)

class SerialFilePlugin(SessionBasedRobustBackendPlugin):
    def __init__(self):
        SessionBasedRobustBackendPlugin.__init__(self)
        self.count = 0
        self.accounting_file = "AccountingFile.txt"

    def open_session(self):
        try:
            return open(self.accounting_file, 'a')
        except IOError, e:
            stderr.write("trouble opening %s %s" %
                         (self.accounting_file, str(e) ) )
            # its sufficient to return None here,
            # SessionBasedRobustBackendPlugin is expecting that, no exception
            # neede
            return None

    def write_to_file(self, msg):
        try:
            self._v_session_active.write(msg)
        except IOError, e:
            stderr.write(str(e))
            raise BoKeepBackendException(str(e))

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
                              attribute_or_blank(line, 'line_memo') )

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
            if hasattr(self, '_v_session_active'):
                self._v_session_active.close()
        except IOError:
            # nothing to do here, super class close() will del
            # self._v_session_active, callers of close are expecting
            # us to silently catch exceptions
            pass
        SessionBasedRobustBackendPlugin.close(self)

    def save(self):
        try:
            self._v_session_active.close()
        except IOError, e:
            stderr.write(str(e))
            raise BoKeepBackendException(str(e.message))
        finally:
            del self._v_session_active
                    
        self.open_session_and_retain()

    def configure_backend(self, parent_window=None):
        cd = SerialFileConfigDialog()
        cd.set_filename(self.accounting_file)
        cd.run()
        self.accounting_file = cd.get_filename()

def get_plugin_class():
    return SerialFilePlugin
