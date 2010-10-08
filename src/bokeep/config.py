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
# ZODB imports
from ZODB.FileStorage import FileStorage
from ZODB import DB

# python imports
from ConfigParser import ConfigParser
from os.path import expanduser, exists

# bokeep imports
from book import BoKeepBookSet

CONFIG_FILE = '.bo-keep.cfg'

CONFIG_HOME = expanduser("~/%s" % CONFIG_FILE)

ZODB_CONFIG_SECTION = 'zodb'
ZODB_CONFIG_FILESTORAGE = 'filestorage'
DEFAULT_BOOKS_PICKLE_DIR = 'bo-keep-database'
DEFAULT_BOOKS_PICKLE_FILE = 'bokeep_books.fs'

DATABASE_VERSION_SUBDB_KEY = 'db_version'

CURRENT_DATABASE_VERSION = '0.4.1'

class BoKeepConfigurationException(Exception):
    pass

class BoKeepConfigurationFileException(BoKeepConfigurationException):
    pass

class BoKeepConfigurationDatabaseException(BoKeepConfigurationException):
    pass

def initialize_config(config):
    config.add_section(ZODB_CONFIG_SECTION)
    config.set(ZODB_CONFIG_SECTION, ZODB_CONFIG_FILESTORAGE,
               expanduser("~/%s/%s" % (DEFAULT_BOOKS_PICKLE_DIR,
                                       DEFAULT_BOOKS_PICKLE_FILE) ) )

def create_config_file(path):
    """Creates a configuration file at path.

    Note, this doesn't care if one is already there, so if this is undisirable
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

def first_config_file_in_list_to_exist_and_parse(files):
    for i,config_file in enumerate(files):
        config = ConfigParser()
        files_read = config.read( [config_file] )
        assert( len(files_read) == 1 or len(files_read) == 0 )
        if len(files_read) == 1:
            return i
    return None

def get_bokeep_config_paths(provided_path=None):
    if provided_path == None:
        return (CONFIG_HOME, CONFIG_FILE)
    else:
        return (provided_path,)    

def get_bokeep_configuration(provided_path=None):
    file_list = get_bokeep_config_paths(provided_path)
        
    good_config = first_config_file_in_list_to_exist_and_parse(file_list)
    if good_config == None:
        raise  BoKeepConfigurationFileException(
            "the specified bokeep configuration file, %s, can not be read" %
            file_list[0] )
    else:
        config = ConfigParser()
        config.read( (file_list[good_config],)) 

    return config
    
def get_bokeep_bookset(provided_config_path=None):
    config = get_bokeep_configuration(provided_config_path)

    if not config.has_option(ZODB_CONFIG_SECTION, ZODB_CONFIG_FILESTORAGE):
        raise BoKeepConfigurationFileException(
            "the bokeep config file %s does not have a zodb filestorage "
            "section" % provided_config_path )
    
    filestorage_path = config.get(ZODB_CONFIG_SECTION, ZODB_CONFIG_FILESTORAGE)

    if not exists(filestorage_path):
        raise BoKeepConfigurationFileException(
            "bokeep database filestorage path %s does not exist" %
            filestorage_path)
    try:
        fs = FileStorage(filestorage_path, create=False )
        bookset = BoKeepBookSet( DB(fs) )
    except IOError, e:
        raise BoKeepConfigurationDatabaseException(
            "there was a problem opening %s: %s" % (
                filestorage_path, e.message )
            )
    else:
        # what about configuration file versioning...?

        db_version = bookset.get_dbhandle().get_sub_database_do_cls_init(
            DATABASE_VERSION_SUBDB_KEY,
            lambda : CURRENT_DATABASE_VERSION,
            )
        if db_version != CURRENT_DATABASE_VERSION:
            raise BoKeepConfigurationDatabaseException(
                "the database versions don't match, %s is db and %s is code" %
                (db_version, CURRENT_DATABASE_VERSION ) )
        return bookset

    # never expected to reach here, except block is supposed to re-throw
    # else block is reponsible for return
    assert(False)

    
