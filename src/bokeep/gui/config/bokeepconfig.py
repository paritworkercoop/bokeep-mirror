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
# python imports
from os.path import exists

# BoKeep imports
from bokeep.config import BoKeepConfigurationFileException, create_config_file  

def answer_yes(msg):
    answer = raw_input(msg + " (y/n)\n> ")
    return answer in ("Yes", "yes", "y", "Y")
        

def establish_bokeep_config(mainwindow, paths, config_exception):
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
                
