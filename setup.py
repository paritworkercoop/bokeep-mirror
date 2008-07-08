#!/usr/bin/env python

from distutils.core import setup

setup(name='Bo-Keep',
      version='0.1',
      scripts=['bo-keep.py', 'bo-keep-book-add.py', 'bo-keep-book-remove.py'],
      packages=['bokeep', 'bokeep.backend_modules', 'bokeep.gui' ],
      package_dir={'bokeep': 'src/bokeep'},
      package_data={'bokeep': ['gui/glade/bokeep_main_window.glade'] },
      )
