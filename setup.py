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
            # don't run tests for the gnucash2.2 backend
            if not t.endswith('__init__.py') and \
                not t.endswith('test_gnucash_backend22.py') and \
                not t.endswith('test_transaction.py')
            )
    
    def run(self):
        sys.path.insert(0, os.path.join(self._dir, BOKEEP_SRC_DIR) )
        sys.path.insert(0, os.path.join(self._dir, 'tests') )
        tests = list(self.generate_test_files())
        tests = TestLoader().loadTestsFromNames( tests )
        t = TextTestRunner(verbosity = 1)
        t.run(tests)

# if you're thinking of changing name='Bo-Keep' to name=PACKAGE_NAME, think
# twice, what's going to happen when you do a setup.py install on top of
# an old installation?
setup(name='Bo-Keep',
      version='1.0.0',
      cmdclass = { 'test': TestCommand },
      scripts=['bo-keep', 
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
                ],
      package_dir={PACKAGE_NAME:
                       os.path.join(BOKEEP_SRC_DIR, PACKAGE_NAME) },
      package_data={PACKAGE_NAME: [
            'gui/bokeep_main_window.glade',
            'gui/bo-keep.svg',
            'plugins/trust/GUIs/management/data/trustor_transactions.glade',
            'plugins/trust/GUIs/management/data/trustor_management.glade',
            'plugins/trust/GUIs/entry/data/trustor_entry.glade',
            'plugins/payroll/payroll.glade',
            'plugins/mileage.glade'] },
      data_files=[('share/applications',
                   ['bo-keep.desktop' ])
                  ]
      )
