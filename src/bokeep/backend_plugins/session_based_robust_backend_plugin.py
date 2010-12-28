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

from robust_backend_plugin import RobustBackendPlugin

#from plugin import \
#@    BackendPlugin, BoKeepBackendException, BoKeepBackendResetException

import transaction

class SessionBasedRobustBackendPlugin(RobustBackendPlugin):
    def open_session_and_retain(self):
        if not self.__has_active_session_attr():
            self._v_session_active = self.open_session()

    def flush_backend(self):
        self.open_session_and_retain()
        if not self.can_write():
            self.close()
        else:
            RobustBackendPlugin.flush_backend(self)

    def close(self, close_reason='reset because close() was called'):
        RobustBackendPlugin.close(self, close_reason)
        if self.__has_active_session_attr():
            del self._v_session_active

    def __has_active_session_attr(self):
        return hasattr(self, '_v_session_active')
    
    def open_session(self):
        raise Exception("robust session based backend plugins must implement "
                        "open_session")

    def can_write(self):
        return self.__has_active_session_attr() and self._v_session_active!=None
    
