#!/usr/bin/env python

from distutils.core import setup

setup(name='Bo-Keep',
      version='0.1',
      scripts=['bo-keep', 'bo-keep-book-add', 'bo-keep-book-remove',
               'bo_keep_module_control', 'bo_keep_payroll.py'],
      packages=['bokeep', 'bokeep.backend_modules', 'bokeep.gui' ],
      package_dir={'bokeep': 'src/bokeep'},
      package_data={'bokeep': ['gui/glade/bokeep_main_window.glade'] },
      )
