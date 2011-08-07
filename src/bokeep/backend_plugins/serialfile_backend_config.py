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

from gtk import FileChooserDialog, FILE_CHOOSER_ACTION_SAVE, RESPONSE_OK, \
    FileFilter, STOCK_CANCEL, RESPONSE_CANCEL, STOCK_SAVE

from bokeep.gui.gladesupport.glade_util import \
    load_glade_file_get_widgets_and_connect_signals

class SerialFileConfigDialog(object):
    """Responsible for creating, setting/getting values of, and destroying the
    SerialFile configuration view."""
    
    def __init__(self):
        self.set_filename(None)
    
    def run(self):
        # Load the view into this class.
        import gnucash_backend_config as gnucash_backend_config_module
        module_path = gnucash_backend_config_module.__file__
        glade_file = join(dirname(abspath(module_path)),
                          'serialfile_backend_config.glade')
        load_glade_file_get_widgets_and_connect_signals(
            glade_file,
            'serialfile_config_dialog',
            self,
            self)
        
        # Populate defaults.
        if self.get_filename() != None:
            self.file_info.set_text(self.get_filename())
        self.__update_acceptableness()
        
        # Give the user a chance to change the attributes of this configuration.
        r = self.serialfile_config_dialog.run()
        if r == RESPONSE_OK:
            self.set_filename(self.file_info.get_text())
        
        self.serialfile_config_dialog.destroy()
        
    def set_filename(self, filename):
        self.filename = filename
        
    def get_filename(self):
        return self.filename
    
    def on_file_button_clicked(self, *args):
        # libglade 2.24 seems to have a bug where if a FileChooserButton is
        # actioned to show a save dialog, a open dialog is still used!  To get
        # around this we use a label, button, and FileChooserDialog instead.
        
        fcd = FileChooserDialog(
            title = "Where should the serial file be?",
            action = FILE_CHOOSER_ACTION_SAVE,
            buttons = (STOCK_CANCEL, RESPONSE_CANCEL, STOCK_SAVE, RESPONSE_OK) )
        
        # Add a GnuCash book filter to the book browsing dialog.
        # (Can't be done with libglade XML files.)
        filter = FileFilter()
        filter.set_name("SerialFile")
        filter.add_pattern("*.txt")
        fcd.add_filter(filter)
        
        result = fcd.run()
        if result == RESPONSE_OK:
            self.file_info.set_text(fcd.get_filename())
        fcd.destroy()
        
        self.__update_acceptableness()
    
    def __update_acceptableness(self):
        """Enables or disables the OK button depending on the acceptableness of
        the proposed configuration."""
        
        if self.file_info.get_text() == None:
            self.ok_button.set_sensitive(False)
        else:
            self.ok_button.set_sensitive(True)