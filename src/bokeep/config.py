from ConfigParser import ConfigParser

from os.path import expanduser

CONFIG_FILE = '.bo-keep.cfg'

def get_database_cfg_file():
    config = ConfigParser()
    config.read( [CONFIG_FILE, expanduser("~/%s" % CONFIG_FILE) ] )

    return config.get("database", "booksdatabase")

        
