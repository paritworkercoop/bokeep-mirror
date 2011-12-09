#!/usr/bin/env python

# Copyright (C) 2009-2011  ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
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


from glob import glob
from os.path import splitext, basename
import os
import os.path
import sys

from distutils.core import setup, Command
from unittest import TextTestRunner, TestLoader

TESTS_DIR = 'tests'

BOKEEP_SRC_DIR = 'src'
PACKAGE_NAME = 'bokeep'

class TestCommand(Command):
    # modified from the code at this article:
    #http://da44en.wordpress.com/2002/11/22/using-distutils/

    user_options = [ ]
    
    def initialize_options(self):
        self._dir = os.getcwd()
        
    def finalize_options(self):
        pass

    def generate_test_files(self):
        return ( 
            "%s.%s" % ( TESTS_DIR, splitext(basename(t))[0])
            for t in glob(os.path.join(self._dir, TESTS_DIR, '*.py'))
            # don't run tests files that cause trouble
            if all( not t.endswith(bad_file)
                    for bad_file in (
                    '__init__.py', 'test_transaction.py',
                    'test_gnucash_backend_via_book.py') )
            )
    
    def run(self):
        sys.path.insert(0, os.path.join(self._dir, BOKEEP_SRC_DIR) )
        sys.path.insert(0, os.path.join(self._dir, 'tests') )
        tests = list(self.generate_test_files())
        tests = TestLoader().loadTestsFromNames( tests )
        t = TextTestRunner(verbosity = 1)
        t.run(tests)

setup(name=PACKAGE_NAME,
      version='1.1.2',
      cmdclass = { 'test': TestCommand },
      scripts=['bo-keep', 
               ],
      url="http://parit.ca/",
      maintainer="Mark Jenkins",
      maintainer_email="mark@parit.ca",
      packages=[PACKAGE_NAME,
                PACKAGE_NAME + '.backend_plugins',
                PACKAGE_NAME + '.gui',
                PACKAGE_NAME + '.gui.config',
                PACKAGE_NAME + '.gui.gladesupport',
                PACKAGE_NAME + '.shells',
                PACKAGE_NAME + '.plugins',
                PACKAGE_NAME + '.plugins.memberfee',
                PACKAGE_NAME + '.plugins.mileage',
                PACKAGE_NAME + '.plugins.payroll',
                PACKAGE_NAME + '.plugins.payroll.canada',
                PACKAGE_NAME + '.plugins.payroll.gui',
                PACKAGE_NAME + '.plugins.timelog',
                PACKAGE_NAME + '.plugins.trust',
                PACKAGE_NAME + '.plugins.trust.GUIs',
                PACKAGE_NAME + '.plugins.trust.GUIs.entry',
                PACKAGE_NAME + '.plugins.trust.GUIs.management',
                ],
      package_dir={PACKAGE_NAME:
                       os.path.join(BOKEEP_SRC_DIR, PACKAGE_NAME) },
      package_data={PACKAGE_NAME: [
            'backend_plugins/gnucash_backend_BOKEEP_BACKEND_PLUGIN',
            'backend_plugins/null_BOKEEP_BACKEND_PLUGIN',
            'backend_plugins/serialfile_BOKEEP_BACKEND_PLUGIN',
            'gui/bokeep_main_window.glade',
            'gui/bo-keep.svg',
            'plugins/trust/BOKEEP_PLUGIN',
            'plugins/trust/GUIs/management/data/trustor_transactions.glade',
            'plugins/trust/GUIs/management/data/trustor_management.glade',
            'plugins/trust/GUIs/entry/data/trustor_entry.glade',
            'plugins/payroll/BOKEEP_PLUGIN',
            'plugins/payroll/gui/payroll.glade',
            'plugins/mileage.glade',
            'plugins/mileage/BOKEEP_PLUGIN'] },
      data_files=[('share/applications',
                   ['bo-keep.desktop' ])
                  ]
      )
