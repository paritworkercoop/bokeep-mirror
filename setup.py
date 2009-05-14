#!/usr/bin/env python

from distutils.core import setup

setup(name='Bo-Keep',
      version='0.2.1',
      scripts=['bo-keep', 'bo-keep-book-add', 'bo-keep-book-remove',
               'bo_keep_module_control', 'bo_keep_payroll.py',
               'initialize_accounting_system.sh', 'edit_bokeep_payroll.sh',
               'run_bokeep_payroll.sh'
               ],
      packages=['bokeep', 'bokeep.backend_modules', 'bokeep.gui',
                'bokeep.modules', 'bokeep.modules.payroll'],
      package_dir={'bokeep': 'src/bokeep'},
      package_data={'bokeep': ['gui/glade/bokeep_main_window.glade'] },
      data_files=[('share/bokeep_initialization',
                   ['.bo-keep.cfg',
                    'examples/bokeep_configuration/books.conf'] ),
                  
                  ('share/bokeep_payroll_examples',
                   ['examples/payroll_configuration/payroll_configuration.py',
                    'examples/payroll_configuration/payday_data.py']
                   ),

                  ('share/bokeep_book_examples',
                   ['examples/books/books.gnucash']),

                  ('share/applications',
                   ['desktop_files/edit_bokeep_payroll.sh.desktop',
                    'desktop_files/run_bokeep_payroll.sh.desktop',
                    'desktop_files/initialize_accounting_system.sh.desktop'
                    ])
                  ]
      )
