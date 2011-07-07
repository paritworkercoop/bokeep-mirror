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
#          Samuel Pauls <samuel@parit.ca>

# This file is responsible for accessing the BoKeep configuration.  It stores
# settings such as plugin directories and the location of the BoKeep books
# database.

# ZODB imports
from ZODB.FileStorage import FileStorage
from ZODB import DB
import ZODB.config # Import in a way that needs ZODB to be prepended to avoid
                   # confusion with general BoKeep config concepts.

# python imports
from ConfigParser import ConfigParser
from os.path import expanduser, exists

# bokeep imports
from book import BoKeepBookSet

CONFIG_FILE = '.bo-keep.cfg'

CONFIG_HOME = expanduser("~/%s" % CONFIG_FILE)

ZODB_CONFIG_SECTION = 'zodb'
DEFAULT_BOOKS_DIR = 'bo-keep-database'
ZODB_CONFIG_FILESTORAGE = 'filestorage'
DEFAULT_BOOKS_FILESTORAGE_FILE = 'bokeep_books.fs'
ZODB_CONFIG_ZCONFIG = 'zconfig'
DEFAULT_BOOKS_ZCONFIG_FILE = 'bokeep_books.conf'

PLUGIN_DIRECTORIES_SECTION = 'plugin_directories'
PLUGIN_DIRECTORIES = 'directories'

DATABASE_VERSION_SUBDB_KEY = 'db_version'

CURRENT_DATABASE_VERSION = '0.4.1'

class BoKeepConfigurationException(Exception):
    pass

class BoKeepConfigurationFileException(BoKeepConfigurationException):
    pass

class BoKeepConfigurationDatabaseException(BoKeepConfigurationException):
    pass

def initialize_config(config):
    """Populate the configuration with default values."""
    
    config.add_section(ZODB_CONFIG_SECTION)
    config.set(ZODB_CONFIG_SECTION, ZODB_CONFIG_FILESTORAGE,
               expanduser("~/%s/%s" % (DEFAULT_BOOKS_DIR,
                                       DEFAULT_BOOKS_FILESTORAGE_FILE) ) )
    config.set(ZODB_CONFIG_SECTION, "# " + ZODB_CONFIG_ZCONFIG,
               expanduser("~/%s/%s" % (DEFAULT_BOOKS_DIR,
                                       DEFAULT_BOOKS_ZCONFIG_FILE) ) )
    
    config.add_section(PLUGIN_DIRECTORIES_SECTION)
    config.set(PLUGIN_DIRECTORIES_SECTION, PLUGIN_DIRECTORIES, [])

def create_config_file(path):
    """Creates a configuration file at path.

    Note, this doesn't care if one is already there, so if this is undesirable
    check for existence before calling this function!
    """
    
    config = ConfigParser()
    initialize_config(config)
    try:
        config_file_handle = file(path, 'w')
        config.write(config_file_handle)
        config_file_handle.close()
    except IOError:
        raise BoKeepConfigurationFileException(
            "The configuration file %s can not be opened for "
            "writing" % path )
    else:
        # if the write process completes without error, there is no way the
        # file can't exist
        assert( exists(path) )
        config = ConfigParser()
        success_reads = config.read( (path,) )
        # if the write process was able to complete without error, there is
        # no way in hell we should have trouble reading it after, especially
        # because initialize_config uses config.set functions..
        assert( len(success_reads) == 1 )

def get_plugins_directories_from_config(config):
    """Returns the directories that front and back-end plugins are located
    in."""
    
    # old versions of bokeep didn't have the plugin directories section
    # so we need to handle that
    if not config.has_option(PLUGIN_DIRECTORIES_SECTION, PLUGIN_DIRECTORIES):
        set_plugin_directories_in_config(config, '[]')
    
    plugin_directories_str = config.get(PLUGIN_DIRECTORIES_SECTION,
                                        PLUGIN_DIRECTORIES)
    if plugin_directories_str == '[]':
        plugin_directories = []
    elif plugin_directories_str.__class__ == list:
        plugin_directories = plugin_directories_str
    else:
        plugin_directories = plugin_directories_str[2:-2].split("', '")
    
    return plugin_directories

def set_plugin_directories_in_config(config, config_path, plugin_directories):
    """Saves the directories that front and back-end plugins are located in."""
    
    if not config.has_section(PLUGIN_DIRECTORIES_SECTION):
        config.add_section(PLUGIN_DIRECTORIES_SECTION)
    config.set(PLUGIN_DIRECTORIES_SECTION, PLUGIN_DIRECTORIES, plugin_directories)
    config_fp = file(config_path, 'w')
    config.write(config_fp)
    config_fp.close()

def first_config_file_in_list_to_exist_and_parse(files):
    for i,config_file in enumerate(files):
        config = ConfigParser()
        files_read = config.read( [config_file] )
        assert( len(files_read) == 1 or len(files_read) == 0 )
        if len(files_read) == 1:
            return config_file
    return None

def get_bokeep_config_paths(provided_config_path=None):
    """Returns all possible BoKeep configuration filenames.
    Note that a particular returned item may not actually exist as a file."""
    
    if provided_config_path == None:
        return (CONFIG_HOME,)
    else:
        return (provided_config_path,)

def get_bokeep_configuration(provided_config_path=None):
    """Return a ConfigParser that represents the BoKeep configuration.
    If no configuration exists, throw a BoKeepConfigurationFileException"""
    
    file_list = get_bokeep_config_paths(provided_config_path)
        
    good_config = first_config_file_in_list_to_exist_and_parse(file_list)
    if good_config == None:
        raise  BoKeepConfigurationFileException(
            "the specified bokeep configuration file, %s, can not be read" %
            file_list[0] )
    else:
        config = ConfigParser()
        config.read( (good_config,)) 

    return config
    
def get_bokeep_bookset(provided_config_path=None):
    """Returns a set of BoKeep books."""
    
    config = get_bokeep_configuration(provided_config_path)
    return get_bokeep_bookset_from_config(provided_config_path, config)

def get_bokeep_bookset_from_config(provided_config_path, config):
    """Returns BoKeep transactions stored in one of several ways.
    
    A BoKeepConfigurationDatabaseException is thrown if a requested file doesn't
    exist or is of an incompatible version."""
    
    if config.has_option(ZODB_CONFIG_SECTION, ZODB_CONFIG_FILESTORAGE):
        filestorage_path = config.get(ZODB_CONFIG_SECTION, ZODB_CONFIG_FILESTORAGE)
        bookset = get_bokeep_bookset_from_filestorage(filestorage_path)
    elif config.has_option(ZODB_CONFIG_SECTION, ZODB_CONFIG_ZCONFIG):
        zconfig_path = config.get(ZODB_CONFIG_SECTION, ZODB_CONFIG_ZCONFIG)
        bookset = get_bokeep_bookset_from_zconfig(zconfig_path)
    else:
        raise BoKeepConfigurationFileException(
            "the bokeep config file %s does not have a %s or %s attribute in "
            "the %s section" % (provided_config_path,
                                ZODB_CONFIG_FILESTORAGE,
                                ZODB_CONFIG_ZCONFIG,
                                ZODB_CONFIG_SECTION) )
    
    # Ensure the loaded BoKeep transaction database's version is compatible
    # with this version of BoKeep. 
    db_version = bookset.get_dbhandle().get_sub_database_do_cls_init(
        DATABASE_VERSION_SUBDB_KEY,
        lambda : CURRENT_DATABASE_VERSION,
        )
    if db_version != CURRENT_DATABASE_VERSION:
        raise BoKeepConfigurationDatabaseException(
            "the database versions don't match, %s is db and %s is code" %
            (db_version, CURRENT_DATABASE_VERSION ) )
    
    return bookset
    
def get_bokeep_bookset_from_filestorage(filestorage_path):
    """Returns BoKeep transactions stored in a file.
    
    A BoKeepConfigurationDatabaseException is thrown if a requested file doesn't
    exist."""
    
    # Ensure the file storage path exists.
    if not exists(filestorage_path):
        raise BoKeepConfigurationDatabaseException(
            "bokeep database filestorage path %s does not exist" %
            filestorage_path)
    
    try:
        fs = FileStorage(filestorage_path, create=False )
        return BoKeepBookSet( DB(fs) )
    except IOError, e:
        raise BoKeepConfigurationDatabaseException(
            "there was a problem opening the filestorage path %s: %s"
            % (filestorage_path, e.message)
            )
    # never reaches this point

def get_bokeep_bookset_from_zconfig(zconfig_path):
    """Returns BoKeep transactions described by a Zope configuration file.
    
    A BoKeepConfigurationDatabaseException is thrown if a requested file doesn't
    exist."""
    
    # Ensure the zconfig path exists.
    if not exists(zconfig_path):
        raise BoKeepConfigurationDatabaseException(
            "bokeep database zope config path %s does not exist" %
            zconfig_path)
    
    try:
        return BoKeepBookSet(ZODB.config.databaseFromURL(zconfig_path))
    except IOError, e:
        raise BoKeepConfigurationDatabaseException(
            "there was a problem opening the zconfig path %s: %s"
            % (zconfig_path, e.message)
            )
    # never reaches this point