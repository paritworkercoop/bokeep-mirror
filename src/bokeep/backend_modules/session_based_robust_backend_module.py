from robust_backend_module import RobustBackendModule

#from module import \
#@    BackendModule, BoKeepBackendException, BoKeepBackendResetException

import transaction

class SessionBasedRobustBackendModule(RobustBackendModule):
    def flush_backend(self):
        if not self.__has_active_session_attr():
            self._v_session_active = self.open_session()
        if not self.can_write():
            self.close()
        else:
            RobustBackendModule.flush_backend(self)

    def close(self, close_reason='reset because close() was called'):
        RobustBackendModule.close(self, close_reason)
        if self.__has_active_session_attr():
            del self._v_session_active

    def __has_active_session_attr(self):
        return hasattr(self, '_v_session_active')
    
    def open_session(self):
        raise Exception("robust session based backend modules must implement "
                        "open_session")

    def can_write(self):
        return self.__has_active_session_attr() and self._v_session_active!=None
    
