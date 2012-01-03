# Copyright (C) 2010-2011  ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
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
#          Sara Arenson <sara_arenson@yahoo.ca>
#          Samuel Pauls <samuel@parit.ca>

# python imports
from os.path import \
    exists, isdir, join as path_join
import os
import sys
from sys import path

# ZODB imports
from ZODB.FileStorage import FileStorage
from ZODB import DB
from ZODB.config import databaseFromURL
import transaction

# gtk imports
from gtk import \
    ListStore, \
    TreeView, TreeViewColumn, CellRendererText, CellRendererToggle, \
    RESPONSE_OK, RESPONSE_CANCEL, RESPONSE_DELETE_EVENT, \
    FILE_CHOOSER_ACTION_SAVE, FileChooserDialog, \
    DIALOG_MODAL, MESSAGE_ERROR, BUTTONS_OK, MessageDialog, \
    STOCK_CANCEL, STOCK_SAVE, FILE_CHOOSER_ACTION_SELECT_FOLDER, \
    Label, STOCK_OK, STOCK_OPEN, Dialog, Button, HBox

# bokeep imports
from bokeep.config import \
    BoKeepConfigurationDatabaseException, ZODB_CONFIG_SECTION, \
    ZODB_CONFIG_FILESTORAGE, get_plugins_directories_from_config, \
    set_plugin_directories_in_config, \
    ZODB_CONFIG_ZCONFIG
from bokeep.book import BoKeepBookSet, FrontendPluginImportError
from bokeep.gui.main_window_glade import get_main_window_glade_file
from bokeep.gui.gladesupport.glade_util import \
    load_glade_file_get_widgets_and_connect_signals

# bokeep.gui.config imports
from state import BoKeepConfigGuiState, \
    DB_ENTRY_CHANGE, DB_PATH_CHANGE, BOOK_CHANGE, BACKEND_PLUGIN_CHANGE, \
    BOOK

def establish_bokeep_db(mainwindow, config_path, config, db_exception):
    """Dialog to edit the configuration settings for a BoKeep database, 
    create it at the configured location if not there yet, and also
    exercise control over other settings kept in the bokeep configuration
    (.bo-keep.cfg), and basic things like creating books and enabling
    plugins.

    And the best part is that a BoKeepBookSet for whichever database
    you choose to select (in this dialog) is returned or None
    if this fails

    mainwindow -- if there's a Gtk.Window we can parrent this dialog too,
                  please provide it, otherwise set to None
    config_path -- path the configuration file is found at
    config     -- a  ConfigParser.ConfigParser pre-loaded with the contents
                  of config_path .
    db_exception -- If you experienced some kind of exception while
                    trying to load the BoKeepBookSet without the help of a
                    this function, pass it on to us so we can display
                    the error to the user so they know why they're
                    being forced into a gui to fix things up

    Changes made to config are saved in config_path
    """
    assert(db_exception == None or
           isinstance(db_exception, BoKeepConfigurationDatabaseException))
    if db_exception == None:
        extra_error_info = None
    else:
        extra_error_info = "%s\n%s" %(
            str(db_exception), 
            "BoKeep requires a working database to operate" )
    
    if config.has_option(ZODB_CONFIG_SECTION, ZODB_CONFIG_FILESTORAGE):
        db_access_method = ZODB_CONFIG_FILESTORAGE
        db_path = config.get(ZODB_CONFIG_SECTION, ZODB_CONFIG_FILESTORAGE)
    elif config.has_option(ZODB_CONFIG_SECTION, ZODB_CONFIG_ZCONFIG):
        db_access_method = ZODB_CONFIG_ZCONFIG
        db_path = config.get(ZODB_CONFIG_SECTION, ZODB_CONFIG_ZCONFIG)
    config_dialog = BoKeepConfigDialog(db_path, db_access_method,
                                       config_path, config,
                                       extra_error_info)
    result, new_db_path, new_db_access_method = config_dialog.run()
    
    assert( result == RESPONSE_OK or result==RESPONSE_CANCEL or
            result==RESPONSE_DELETE_EVENT )
    if new_db_path == None or result!=RESPONSE_OK:
        return None

    # should save new_db_path in config if different
    if new_db_path != db_path or \
            new_db_access_method != db_access_method:
        if new_db_access_method == ZODB_CONFIG_FILESTORAGE:
            config.set(ZODB_CONFIG_SECTION, ZODB_CONFIG_FILESTORAGE,
                       new_db_path)
            config.remove_option(ZODB_CONFIG_SECTION, ZODB_CONFIG_ZCONFIG)
        elif new_db_access_method == ZODB_CONFIG_ZCONFIG:
            config.set(ZODB_CONFIG_SECTION, ZODB_CONFIG_ZCONFIG,
                       new_db_path)
            config.remove_option(ZODB_CONFIG_SECTION, ZODB_CONFIG_FILESTORAGE)
        config_fp = file(config_path, 'w')
        config.write(config_fp)
        config_fp.close()

    if new_db_access_method == ZODB_CONFIG_FILESTORAGE:
        return BoKeepBookSet(DB(FileStorage(new_db_path, create=False)))
    elif new_db_access_method == ZODB_CONFIG_ZCONFIG:
        return BoKeepBookSet(databaseFromURL(new_db_path))

def get_available_frontend_plugins():
    return available_plugins_search("BOKEEP_PLUGIN", "plugins")

def get_available_backend_plugins():
    return available_plugins_search("BOKEEP_BACKEND_PLUGIN", "backend_plugins")

def available_plugins_search(plugin_file_name, plugin_subdir):

    """Returns a list of plugins, automatically detected.

    Searches all directories in python path, plus /bokeep/plugins in each of these 
    directories.

    A module [name].py is a plugin if there's a corresponding file called 
    [name]_[plugin_file_name] in the same directory, e.g. [name]_BOKEEP_PLUGIN if
    plugin_file_name=BOKEEP_PLUGIN.

    A package is a plugin if there's a [plugin_file_name] file in its base directory. 
    e.g. package name payroll has directory payroll/, plugin_file_name=BOKEEP_PLUGIN,
    and file payroll/BOKEEP_PLUGIN exists.

    The [plugin_file_name] files are empty.
    """
    dir_list = [ directory 
                 for directory in sys.path
                 if exists(directory) ]
    dir_list.extend([ path_join(directory, "bokeep", plugin_subdir) 
                      for directory in dir_list
                      if ( isdir(path_join(directory, "bokeep", plugin_subdir))
                           and 
                           exists(path_join(directory, "bokeep", plugin_subdir))
                           ) # end and expression
                      ])

    bokeep_packages = []
    bokeep_modules = []

    for directory in dir_list:
        if not isdir(directory):
            continue # very lazy of me to use a GOTO...
        items = set(os.listdir(directory))
        sub_directories = set([ item
                                for item in items 
                                if isdir(path_join(directory, item)) ])

        new_packages = [ sub_dir
                         for sub_dir in sub_directories
                         if exists( 
                             path_join(directory, sub_dir, plugin_file_name)) ]     
        
        module_names = [ item[0:item.index("_"+plugin_file_name)]
                         for item in items.difference(sub_directories)
                         if item.endswith("_"+plugin_file_name) ]

        new_modules = [ module_name 
                        for module_name in module_names
                        if exists( path_join(directory, module_name+".py") ) ]

        if directory.endswith(path_join("bokeep", plugin_subdir)):
            new_packages = [ "bokeep." + plugin_subdir + "." + name 
                              for name in new_packages]
            new_modules = [ "bokeep."  + plugin_subdir + "." + name 
                              for name in new_modules]

        bokeep_packages.extend(new_packages)
        bokeep_modules.extend(new_modules)

    return bokeep_packages + bokeep_modules

class BoKeepConfigDialog(object):
    """GUI for configuring BoKeep."""
    
    config_path = None
    config = None
    
    def __init__(self,
                 db_path, db_access_method,
                 config_path, config,
                 error_msg=None):
        self.config_path = config_path
        self.config = config
        
        load_glade_file_get_widgets_and_connect_signals(
            get_main_window_glade_file(), "bokeep_config_dialog",
            self, self)
        self.selection_change_lock = True

        self.state = BoKeepConfigGuiState(
            error_msg, self.__force_config_on_newly_created_plugin)
        self.books_tv = TreeView(self.state.book_liststore)
        self.books_tv.append_column(
                TreeViewColumn("Book", CellRendererText(), text=0 ) )
        self.books_tv.get_selection().connect(
            "changed", self.on_book_selection_change)
        self.books_window.add(self.books_tv)
        self.books_tv.show()
        self.plugins_tv = TreeView(self.state.frontend_plugin_liststore)
        self.plugins_tv.append_column(
            TreeViewColumn("Plugin", CellRendererText(), text=0) )
        crt = CellRendererToggle()
        crt.set_radio(False)
        self.plugins_tv.append_column(
            TreeViewColumn("Enabled", crt, active=1) )
        self.plugins_window.add(self.plugins_tv)
        self.plugins_tv.show()
        self.plugin_directories_button.connect('clicked',
                            self.__on_plugin_directories_button_click)

        self.__populate_possible_plugins()

        self.db_path_label.set_text(db_path)
        if db_path != None:
            self.do_action(DB_ENTRY_CHANGE, (db_path, db_access_method))
            self.do_action(DB_PATH_CHANGE)
        
        if db_access_method == ZODB_CONFIG_FILESTORAGE:
            self.filestorage_radio.set_active(True)
        elif db_access_method == ZODB_CONFIG_ZCONFIG:
            self.zconfig_radio.set_active(True)

        if error_msg == None:
            error_msg = ""
        self.message_label.set_label(error_msg)

        self.set_sensitivities()
        self.selection_change_lock = False
        self.backend_entry_lock = False
        
    def __populate_possible_plugins(self):
        """Populates the GUI with the possible front and backend plugins."""
        
        available_plugin_liststore = ListStore(str)
        for plugin_name in get_available_frontend_plugins():
            available_plugin_liststore.append([plugin_name])
        self.plugin_add_entry_combo.set_model(available_plugin_liststore)
        self.plugin_add_entry_combo.set_text_column(0)

        available_backend_plugin_liststore = ListStore(str)
        for backend_plugin_name in get_available_backend_plugins():
            available_backend_plugin_liststore.append([backend_plugin_name])
        self.backend_plugin_entry_combo.set_model(available_backend_plugin_liststore)
        self.backend_plugin_entry_combo.set_text_column(0)

    def do_action(self, action, arg=None):
        """Passes on an action to BoKeepConfigGuiState and gui is then
        updated after to reflect the effects of that action by examining
        where that state machine is at after the action.
        """
        
        try:
            self.state.do_action(action, arg)
        except FrontendPluginImportError, err:
            backend_plugin_entry = self.backend_plugin_entry_combo.child
            backend_plugin_name = backend_plugin_entry.get_text()
            if backend_plugin_name in err.plugin_names:
                self.backend_plugin_entry_combo.child.set_text(
                        self.state.data[BOOK].get_backend_plugin_name() )
                err.plugin_names.remove(backend_plugin_name)

            frontend_plugins = {}
            for name, enabled in self.state.frontend_plugin_liststore:
                frontend_plugins[name] = (name, enabled)

            for err_plugin_name in err.plugin_names:
                del frontend_plugins[err_plugin_name]

            self.state.frontend_plugin_liststore.clear()
            for valid_plugin_name, enabled in frontend_plugins.values():
                self.state.frontend_plugin_liststore.append((valid_plugin_name, enabled))

            error_dialog = MessageDialog(self.bokeep_config_dialog, DIALOG_MODAL, 
                           MESSAGE_ERROR, BUTTONS_OK, str(err))
            error_dialog.run()
            error_dialog.destroy()
            # raises last exception that had been caught, in above
            # except clause, err
            raise


    def __get_db_access_method(self):
        if self.filestorage_radio.get_active():
            db_access_method = ZODB_CONFIG_FILESTORAGE
        elif self.zconfig_radio.get_active():
            db_access_method = ZODB_CONFIG_ZCONFIG
        return db_access_method

    def run(self):
        """Run the BoKeep configuration dialog so the user can interact with
        it."""
        
        self.bokeep_config_dialog.run()
        if self.state.action_allowed(BOOK_CHANGE):
            self.do_action(BOOK_CHANGE, None)
        self.state.close()
        
        db_path = self.db_path_label.get_text()
        db_access_method = self.__get_db_access_method()
        
        self.bokeep_config_dialog.destroy()

        return RESPONSE_OK, db_path, db_access_method

    def set_sensitivities(self):
        """Set the enabled/disabled property of all config widgets."""
        
        for obj, action in (
            (self.books_tv, BOOK_CHANGE),
            (self.book_add_entry, BOOK_CHANGE),
            (self.book_add_button, BOOK_CHANGE),
            (self.plugins_tv, BACKEND_PLUGIN_CHANGE),
            (self.plugin_add_entry_combo, BACKEND_PLUGIN_CHANGE),
            (self.plugin_add_button, BACKEND_PLUGIN_CHANGE),
            (self.backend_plugin_entry_combo, BACKEND_PLUGIN_CHANGE),
            ):
            obj.set_sensitive( self.state.action_allowed(action) )

    def get_currently_selected_book(self, *args):
        """Return the currently selected book in the configuration dialog."""
        
        sel = self.books_tv.get_selection()
        sel_iter = sel.get_selected()[1]
        if sel_iter == None:
            return None
        else:
            sel_row = self.state.book_liststore[sel_iter]
            return sel_row[0]

    def select_book(self, new_book):
        """Visually select a given book in the configuration dialog."""
        
        selection = self.books_tv.get_selection()
        selection.unselect_all()
        for path, book in enumerate(self.state.book_liststore):
            if book[0] == new_book.book_name:
                selection.select_path(path)
                break

    # event handles

    def on_selectdb_button_clicked(self, *args):
        """Browse for the location of a new BoKeep transaction database."""
        
        fcd = FileChooserDialog(
            "Where should the database be?",
            self.bokeep_config_dialog,
            FILE_CHOOSER_ACTION_SAVE,
            (STOCK_CANCEL, RESPONSE_CANCEL, STOCK_SAVE, RESPONSE_OK) )
        fcd.set_modal(True)
        result = fcd.run()
        db_path = fcd.get_filename()
        fcd.destroy()
        if result == RESPONSE_OK and db_path != None:
            self.db_path_label.set_text(db_path)
            db_access_method = self.__get_db_access_method()
            self.__update_db_path(db_path, db_access_method)
            self.set_sensitivities()

    def on_book_add_entry_clicked(self, *args):
        self.books_tv.get_selection().unselect_all()
        self.selection_change_lock = True
        self.do_action(BOOK_CHANGE, None)
        self.selection_change_lock = False
        self.set_sensitivities()

    def on_book_add_clicked(self, *args):
        new_book = self.book_add_entry.get_text()
        self.state.book_liststore.append( (new_book,))
        self.book_add_entry.set_text("")
        cur_book = self.get_currently_selected_book()
        # this ensures the book get added
        self.do_action(BOOK_CHANGE, new_book)
        self.do_action(BOOK_CHANGE, cur_book)

    def on_plugin_add_clicked(self, *args):
        entry = self.plugin_add_entry_combo.child
        self.state.frontend_plugin_liststore.append((entry.get_text(), True))
        entry.set_text("")

    def on_backend_plugin_entry_combo_changed(self, *args):
        if not self.backend_entry_lock:
            entry = self.backend_plugin_entry_combo.child
            self.do_action(BACKEND_PLUGIN_CHANGE, entry.get_text())

    def on_book_selection_change(self, *args):
        if not self.selection_change_lock:
            sel_book = self.get_currently_selected_book()
            if sel_book == None:
                try:
                    self.do_action(BOOK_CHANGE, None)
                except FrontendPluginImportError:
                    self.select_book(self.state.data[BOOK])
                else:
                    self.backend_entry_lock = True
                    self.backend_plugin_entry_combo.child.set_text("")
                    self.backend_entry_lock = False
            else:
                try:
                    self.do_action(BOOK_CHANGE, sel_book)
                except FrontendPluginImportError:
                    self.select_book(self.state.data[BOOK])
                else:
                    self.backend_entry_lock = True
                    self.backend_plugin_entry_combo.child.set_text(
                        self.state.data[BOOK].get_backend_plugin_name() )
                    self.backend_entry_lock = False
            self.set_sensitivities()
            
    def on_storage_method_radio_toggled(self, *args):
        """Should be called when the database storage method changes.  For
        example, when the database was referenced directly by file storage and
        changed to a reference through a Zope configuration.
        
        At this time the location used for the database is updated."""
        
        location = self.db_path_label.get_text()
        FILESTORAGE_EXTENSION = ".fs"
        ZCONF_EXTENSION = ".conf"
        if self.filestorage_radio.get_active():
            # Toggle the extension from ZConfig to FS.
            if location.endswith(ZCONF_EXTENSION):
                location = location[:-len(ZCONF_EXTENSION)]
            if not location.endswith(FILESTORAGE_EXTENSION):
                location += FILESTORAGE_EXTENSION
            
            access_method = ZODB_CONFIG_FILESTORAGE
        else:
            # Toggle the extension from FS to ZConfig.
            if location.endswith(FILESTORAGE_EXTENSION):
                location = location[:-len(FILESTORAGE_EXTENSION)]
            if not location.endswith(ZCONF_EXTENSION):
                location += ZCONF_EXTENSION
            
            access_method = ZODB_CONFIG_ZCONFIG
        self.db_path_label.set_text(location)
        
        self.__update_db_path(location, access_method)
    
    def __update_db_path(self, db_path, access_method):
        """Updates the storage location and method of BoKeep's transaction
        database."""
        
        # Prevent the book selection widget from issuing events that change
        # things beyond what we manually want the state machine to handle at the
        # moment.
        self.selection_change_lock = True
        
        # TODO: The following two config state machine actions (DB_ENTRY_CHANGE
        # and DB_PATH_CHANGE) should be merged.  They're split because the
        # BoKeep configuration GUI used to have a text entry widget for the
        # transaction database path.
        
        # Update the transaction storage location.
        self.do_action(DB_ENTRY_CHANGE, (db_path, access_method))
        
        # Commit the transaction storage location.
        self.do_action(DB_PATH_CHANGE)
        
        self.selection_change_lock = False
        
    def __on_plugin_directories_button_click(self, button):
        """Present a dialog to the user for selecting extra plugin directories
        and process the request."""
        
        dia = Dialog('Plugin Directories',
             None, DIALOG_MODAL,
             (STOCK_OK, RESPONSE_OK,
             STOCK_CANCEL, RESPONSE_CANCEL ) )
        dia.resize(500, 300)
        dia.vbox.set_spacing(8)
        
        # Setup the tree view of plugin directories.
        model = ListStore(str) # each row contains a single string
        tv = TreeView(model)
        cell = CellRendererText()
        column = TreeViewColumn('Directory', cell, text = 0)
        tv.append_column(column)
        dia.vbox.pack_start(tv)
        
        # Populate the tree view.
        plugin_directories = \
            get_plugins_directories_from_config(self.config, self.config_path)
        for plugin_directory in plugin_directories:
            row = (plugin_directory,)
            model.append(row)
        
        modify_box = HBox(spacing = 8)
        
        # Setup the remove directory button.
        remove_button = Button('Remove')
        remove_button.set_sensitive(False) # no directory selected initially
        remove_button.connect('clicked', self.__on_remove, tv)
        modify_box.pack_end(remove_button, expand = False)
        
        tv.connect('cursor-changed', self.__on_select, remove_button)
        
        # Setup the add directory button.
        add_button = Button('Add')
        add_button.connect('clicked', self.__on_add, tv)
        modify_box.pack_end(add_button, expand = False)
        
        dia.vbox.pack_start(modify_box, expand = False)
        
        # Setup the "already included directories" label.
        included_label = Label('Plugins in the PYTHONPATH are already ' +
                               'available to BoKeep.')
        # Use a horizontal box to left-justify the label.  For some reason,
        # the label's set_justification property doesn't work for me.
        label_box = HBox()
        label_box.pack_start(included_label, expand = False)
        dia.vbox.pack_start(label_box, expand = False)
        
        dia.show_all()
        dia_result = dia.run()
        
        if dia_result == RESPONSE_OK:            
            # Remove the old plugin directories from the program's path.
            plugin_directories = \
                get_plugins_directories_from_config(self.config,
                                                    self.config_path)
            for plugin_directory in plugin_directories:
                path.remove(plugin_directory)
            
            # Get the new plugin directories from the dialog.
            plugin_directories = []
            for row in model:
                plugin_directory = row[0]
                plugin_directories.append(plugin_directory)
            
            # Update the BoKeep PYTHONPATH so that new plugins can be loaded and
            # populate the list of possible new plugins.
            for plugin_directory in plugin_directories:
                path.append(plugin_directory)
            self.__populate_possible_plugins()
            
            # Save the new plugin directories in the configuration file.
            set_plugin_directories_in_config(self.config,
                self.config_path, plugin_directories)
        
        dia.destroy()
    
    def __on_add(self, button, tree_view):
        file_chooser = FileChooserDialog('Add Plugin Path', None, FILE_CHOOSER_ACTION_SELECT_FOLDER,
                    (STOCK_CANCEL, RESPONSE_CANCEL, STOCK_OPEN, RESPONSE_OK) )
        result = file_chooser.run()
        model = tree_view.get_model()
        if result == RESPONSE_OK:
            row = (file_chooser.get_filename(),)
            model.append(row)
            
        file_chooser.destroy()
    
    def __on_remove(self, button, tree_view):
        model, iter = tree_view.get_selection().get_selected()
        model.remove(iter)
        
        # Disable the remove button as no row is selected after deletion.
        button.set_sensitive(False)
        
    def __on_select(self, tree_view, remove_button):
        model, iter = tree_view.get_selection().get_selected()
        # Just changing the cursor doesn't necessarily mean that a row was
        # selected.
        if iter != None:
            remove_button.set_sensitive(True)

    def __force_config_on_newly_created_plugin(self, book, is_backend, new_plugin):
        """Configures a newly added frontend plugin.
        
        book: The BoKeep book that the plugin is used in.
        is_backend: True if it's a backend plugin, False if frontend.
        new_plugin: The new plugin that needs configuring."""
        
        if is_backend:
            new_plugin.configure_backend(self.bokeep_config_dialog)
        else:
            new_plugin.run_configuration_interface(
                self.bokeep_config_dialog,
                book.get_backend_plugin().backend_account_dialog,
                book)
