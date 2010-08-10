#!/usr/bin/env python

from distutils.core import setup

setup(name='parrot_house_money',
      scripts=['parrot_house_money'],
      packages=['parrot_house_money'],
      package_dir={'parrot_house_money': 'src'},
      package_data={'parrot_house_money': ['data/parrot_house_money.glade'] },
      )
