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
# Author: Samuel Pauls <samuel@parit.ca>

from os.path import join, dirname, abspath

from gtk import RESPONSE_OK, FileFilter

from bokeep.gui.gladesupport.glade_util import \
    load_glade_file_get_widgets_and_connect_signals

class GnuCashConfigDialog(object):
    def __init__(self):
        self.set_book_filename(None)
    
    def run(self):
        # Load the view into this class.
        import gnucash_backend_config as gnucash_backend_config_module
        module_path = gnucash_backend_config_module.__file__
        glade_file = join(dirname(abspath(module_path)),
                          'gnucash_backend_config.glade')
        load_glade_file_get_widgets_and_connect_signals(
            glade_file,
            'gnucash_config_dialog',
            self,
            self)
        
        # Add a GnuCash book filter to the book browsing dialog.
        # (Can't be done with libglade XML files.)
        filter = FileFilter()
        filter.set_name("GnuCash Book")
        filter.add_pattern("*.gnucash")
        self.book_browser.add_filter(filter)
        
        # Populate defaults.
        if self.get_book_filename() != None:
            self.book_browser.set_filename(self.get_book_filename())
        self.__update_acceptableness()
        
        # Give the user a chance to change the attributes of this configuration.
        r = self.gnucash_config_dialog.run()
        if r == RESPONSE_OK:
            self.set_book_filename(self.book_browser.get_filename())
        
        self.gnucash_config_dialog.destroy()
        
    def set_book_filename(self, book_filename):
        self.book_filename = book_filename
        
    def get_book_filename(self):
        return self.book_filename
    
    def on_book_browser_selection_changed(self, *args):
        self.__update_acceptableness()
    
    def __update_acceptableness(self):
        """Enables or disables the OK button depending on the acceptableness of
        the proposed configuration."""
        
        if self.book_browser.get_filename() == None:
            self.ok_button.set_sensitive(False)
        else:
            self.ok_button.set_sensitive(True)