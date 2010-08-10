from gtk import CellRendererText, CellRendererToggle
from util import IntDecimalNumber

class CellRendererTextEditable(CellRendererText):
    def __init__(self, model_col):
        CellRendererText.__init__(self)
        self.connect( "edited", self.edit_callback )
        self.set_property('editable', True)
        self.model_col = model_col

    def edit_callback(self, cell, path, new_text):
        self.model[path][self.model_col] = new_text

class CellRendererNumberEditable(CellRendererTextEditable):
    def edit_callback(self, cell, path, new_text):
        CellRendererTextEditable.edit_callback(self, cell, path, new_text)
        try:
            IntDecimalNumber(new_text)
        except ValueError:
            self.model[path][self.model_col+1] = True
        else:
            self.model[path][self.model_col+1] = False


class CellRendererToggleEditable(CellRendererToggle):
    def __init__(self, model_col):
        CellRendererToggle.__init__(self)
        self.connect( 'toggled', self.toggle_callback )
        self.set_property('activatable', True)
        self.model_col = model_col

    def toggle_callback(self, cell, path ):
        self.model[path][self.model_col] = not self.model[path][self.model_col]
