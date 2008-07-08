from module import BackendModule

class NullBackendModule(BackendModule):
    pass


def get_module_class():
    return NullBackendModule
