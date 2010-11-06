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

from bokeep.util import \
    ends_with_commit, FunctionAndDataDrivenStateMachine, \
    state_machine_do_nothing, state_machine_always_true

# possible actions
(DB_ENTRY_CHANGE, DB_PATH_CHANGE, BOOK_CHANGE, BACKEND_PLUGIN_CHANGE, CLOSE) = \
    range(5)

# tuple indexes for data stored in BoKeepConfigGuiState
(DB_PATH, BOOK) = range(2)

class BoKeepConfigGuiState(FunctionAndDataDrivenStateMachine):
    NUM_STATES = 3
    (
        # There is no working database selected
        NO_DATABASE,
        # There is a working database, but no book selected
        NO_BOOK,
        # There is a book selected on a working database
        BOOK_SELECTED,
        ) = range(NUM_STATES)

    def __init__(self):
        FunctionAndDataDrivenStateMachine.__init__(
            self,
            data=("", None), # DB_PATH, BOOK
            initial_state=BoKeepGuiState.NO_DATABASE)
        self.run_until_steady_state()
        assert(self.state == BoKeepGuiState.NO_DATABASE)

    def get_table(self):
        if hasattr(self, '_v_table_cache'):
            return self._v_table_cache
        
        self._v_table_cache = (
            )
        
        return self._v_table_cache

    
