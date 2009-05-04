from ConfigParser import ConfigParser

from os.path import expanduser

CONFIG_FILE = '.bo-keep.cfg'

def get_database_cfg_file():
    config = ConfigParser()
    config.read( [expanduser("~/%s" % CONFIG_FILE), CONFIG_FILE ] )

    print config.get("database", "booksdatabase")
    return config.get("database", "booksdatabase")

        
