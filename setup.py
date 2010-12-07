#!/usr/bin/env python

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
            if not t.endswith('__init__.py')
            )
    
    def run(self):
        sys.path.insert(0, os.path.join(self._dir, BOKEEP_SRC_DIR) )
        tests = TestLoader().loadTestsFromNames( self.generate_test_files() )
        t = TextTestRunner(verbosity = 1)
        t.run(tests)

# if you're thinking of changing name='Bo-Keep' to name=PACKAGE_NAME, think
# twice, what's going to happen when you do a setup.py install on top of
# an old installation?
setup(name='Bo-Keep',
      version='1.0.0',
      cmdclass = { 'test': TestCommand },
      scripts=['bo-keep', 'bo-keep.sh'
               ],
      packages=[PACKAGE_NAME,
                PACKAGE_NAME + '.backend_plugins',
                PACKAGE_NAME + '.gui',
                PACKAGE_NAME + '.gui.config',
                PACKAGE_NAME + '.gui.gladesupport',
                PACKAGE_NAME + '.plugins',
                PACKAGE_NAME + '.plugins.payroll',
                PACKAGE_NAME + '.plugins.payroll.canada',
                PACKAGE_NAME + '.plugins.trust',
                PACKAGE_NAME + '.plugins.trust.GUIs',
                PACKAGE_NAME + '.plugins.trust.GUIs.entry',
                PACKAGE_NAME + '.plugins.trust.GUIs.management',
                PACKAGE_NAME + '.plugins.mileage',
                ],
      package_dir={PACKAGE_NAME:
                       os.path.join(BOKEEP_SRC_DIR, PACKAGE_NAME) },
      package_data={PACKAGE_NAME: [
            'gui/glade/bokeep_main_window.glade',
            'gui/glade/bokeep.ico',
            'gui/bo-keep.svg',
            'plugins/trust/GUIs/management/data/trustor_transactions.glade',
            'plugins/trust/GUIs/management/data/trustor_management.glade',
            'plugins/trust/GUIs/entry/data/trustor_entry.glade',
            'plugins/mileage/mileage.glade'] },
      data_files=[('share/applications',
                   ['desktop_files/bo-keep.sh.desktop' ])
                  ]
      )
