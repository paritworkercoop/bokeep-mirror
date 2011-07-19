# Copyright (C) 2011  ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
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

# gtk imports
from gtk import Window, VBox

class SimpleTransactionEditor(object):   
    def __init__(self, trans, transid, plugin, gui_parent,
                 change_register_function, book):
        """Sub classes should not override this __init__ but instead
        implement simple_init_before_show() to hook in at the right time
        """
        self.trans = trans
        self.transid = transid
        self.plugin = plugin
        self.gui_parent = gui_parent
        self.change_register_function = change_register_function
        self.book = book

        # An offscreen place for the transaction's GUI to hide while not in use.
        self.hide_parent = Window()
        self.hide_parent.hide()
        self.mainvbox = VBox()
        self.hide_parent.add(self.mainvbox)

        self.simple_init_before_show()

        self.mainvbox.show_all()
        self.mainvbox.reparent(self.gui_parent)

    def simple_init_before_show(self):
        """Create the GUI for this type of BoKeep transaction.  Widgets can be
        added to the "self.mainvbox" object."""
        
        raise Exception("simple_init_before_show must be overrided by "
                        "sub classes of SimpleTransactionEditor")

    def detach(self):
        """Detach the BoKeep transaction's GUI from the visible window and
        attach it to a hidden window.
        
        Sub classes overriding this are recommended to do their own work first, and
        then delegate back up to this original detach so it may do the widget reparenting
        work"""
        self.mainvbox.reparent(self.hide_parent)
