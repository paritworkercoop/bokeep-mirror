from bokeep.config import BoKeepConfigurationDatbaseException

def establish_bokeep_db(config_path, db_exception):
    assert(db_exception == None or
           isinstance(db_exception, BoKeepConfigurationDatbaseException))
    if db_exception != None:
        print db_exception.message
        print "BoKeep requires a working database to operate"
    return None
