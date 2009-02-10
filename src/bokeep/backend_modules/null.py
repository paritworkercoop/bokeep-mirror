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
