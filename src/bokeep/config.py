# ZODB imports
from ZODB.FileStorage import FileStorage
from ZODB import DB

# python imports
from ConfigParser import ConfigParser
from os.path import expanduser

# bokeep imports
from book import BoKeepBookSet

CONFIG_FILE = '.bo-keep.cfg'

CONFIG_HOME = expanduser("~/%s" % CONFIG_FILE)

ZODB_CONFIG_SECTION = 'zodb'
ZODB_CONFIG_FILESTORAGE = 'filestorage'
DEFAULT_BOOKS_PICKLE_FILE = 'bokeep_books.fs'
DEFAULT_BOOKS_PICKLE_DIR = 'bo-keep'

class BoKeepConfigurationException(Exception):
    pass

def initialize_config(config):
    config.set(ZODB_CONFIG_SECTION, ZODB_CONFIG_FILESTORAGE,
               expanduser("~/%s" % DEFAULT_BOOKS_PICKLE_FILE) )    

def get_bokeep_configuration(provided_path=None):
    config = ConfigParser()
    if provided_path == None:
        success_reads = \
            config.read( [expanduser(
                    "~/%s/%s" % (DEFAULT_BOOKS_PICKLE_DIR, CONFIG_FILE)),
                          CONFIG_FILE ] )
    # else a specific config file is being requested
    else:
        success_reads = config.read( [provided_path] )
        if len(success_reads) == 0:
            raise BoKeepConfigurationException(
                "the specified bokeep configuration file, %s, can not be read"
                % provided_path)

    if len(success_reads) == 0:
        initialize_config(config)
        try:
            config_file = file(CONFIG_HOME, 'w')
        except IOError:
            raise BoKeepConfigurationException(
                "The default configuration file %s can not be opened for "
                "writing" % CONFIG_HOME )
        config.write(config_file)
        config_file.close()
        success_reads = config.read( [CONFIG_HOME] )
        assert( len(success_reads) == 1 )

    config = ConfigParser()
    config.read( [success_reads[0]] )
    return config
    
def get_bokeep_bookset(provided_config_path=None):
    config = get_bokeep_configuration(provided_config_path)
    return BoKeepBookSet(
        DB( FileStorage(
                config.get(ZODB_CONFIG_SECTION, ZODB_CONFIG_FILESTORAGE)) ) )

    
