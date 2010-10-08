# python imports
from os.path import exists

# BoKeep imports
from bokeep.config import BoKeepConfigurationFileException, create_config_file  

def answer_yes(msg):
    answer = raw_input(msg + " (y/n)\n> ")
    return answer in ("Yes", "yes", "y", "Y")
        

def establish_bokeep_config(paths, config_exception):
    assert(isinstance(config_exception, BoKeepConfigurationFileException))
    print config_exception.message
    print "BoKeep requires a configuration file to operate"

    # This is here to support the old default
    # current working directory config vs home directory configs
    # but maybe there should only be one default place to look (home dir)?
    for path in paths:
        if answer_yes("Would you like %s to be created from scratch?" %
                      path):
            # important to make a distinction to the user between
            # creating something from nothing and overwrite
            if exists(path) and not answer_yes(
                "%s already exists, overwrite?" % path):
                    return None
            try:
                create_config_file(path)
            except BoKeepConfigurationFileException, e:
                print path, "could not be created %s" % e.message
            else:
                return path
    # it would be nice if this wasn't communicated in prompt form,
    # If and when this becomes a real GUI, it would be nice if "do nothing"
    # were the obvious default option, perhaps the result of closing the
    # the window / hitting cancel, or even the default option for a radio
    # button set
    print "no configuration file created, goodbye"
    return None
                
