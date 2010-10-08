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
from module import BackendModule

class NullBackendModule(BackendModule):
    def __init__(self):
        BackendModule.__init__(self)
        self.count = 0

    def can_write(self):
        # The NullBackend can always claim to be able to write, because
        # it never needs to
        return True

    def remove_backend_transaction(self, backend_ident):
        # no problem removing backend_ident, nothing to do,
        # but check its legit at least
        assert( backend_ident < self.count )

    def create_backend_transaction(self, fin_trans):
        # just swalow any financial transactions and assign them a number
        return_value = self.count
        self.count+=1
        return return_value

    def save(self):
        # this is nullness incarnate
        pass

def get_module_class():
    return NullBackendModule
