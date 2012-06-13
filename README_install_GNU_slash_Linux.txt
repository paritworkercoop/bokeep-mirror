Before we install Bo-Keep on GNU/Linux we have to install the required
dependencies PyGTK and ZODB. You'll likely want GnuCash as well for a
real backend plugin.

It is assumed you have a GNU/Linux distribution with a Python
interpreter installed. (we've tested the CPython implementation
[http://python.org] versions 2.5, 2.6, and 2.7 it's possible that we've
written Bo-Keep to be 2.4 compatible...)

Almost all distributions package PyGTK (http://pygtk.org/) with glade
support. In Debian based distributions (like gNewSense and Ubuntu) it
is probably already installed as well, but if not:
# aptitude install python-gtk2 python-glade2
should do the tick.  You can check this has
worked with
$ python
>>> import gtk

Debian based distributions also tend to have a package for ZODB 3
(http://www.zodb.org/) like so:
# aptitude install python-zodb

If not, it is easily installable via PyPi with easy_install
http://pypi.python.org/pypi/setuptools

Debian based distros will have
# aptitude install python-setuptools


# easy_install ZODB3
(ends up in /usr/)
or
# easy_install --prefix=/path/to/zodb_install/ ZODB3

If you've installed it to someplace other than /usr/ or /usr/local,
you'll need to set PYTHONPATH to include it
$ export \
PYTHONPATH=/path/to/zodb_install/lib/python2.x/site-packages/:$PYTHONPATH

Test your zodb installation like so
$ python
>>> import transaction
>>> import persistent


In order to use the GnuCash backend in BoKeep you need a build of GnuCash with
python bindings enabled. BoKeep developers are testing against the
build of GnuCash in Ubuntu 12.04 which has python bindings in the
python-gnucash package. There is also a python-gnucash package in debian
unstable, wheezy, and squeeze-backports, but these haven't been tested.
(they should be fine).

To our knowledge, everyone else has to build GnuCash manually to end up with
python bindings. You may find 
http://wiki.gnucash.org/wiki/GnuCash#Installation to be helpful;
included are instructions for other distros.

Include --enable-python-bindings in your invocation of configure.

To use the Python bindings, you need to either install GnuCash in a
place like /usr/ or /usr/local where your Python interpreter can find
it such as creating a .pth file, or set the PYTHONPATH environmental variable
$ export PYTHONPATH=/opt/gnucash-2.4.0/lib/python2.x/site-packages/:$PYTHONPATH

Test the python bindings out:
$ python
>>> import gnucash

Bo-keep can be installed with its setup.py script like so # python
setup.py install or
# python setup.py install \
--prefix=/path/to/where/you/want/bokeep/

We're make a python egg available in PyPi and provide a debian package
to make this even easier eventually.

If you haven't installed it to /usr/ or /usr/local, python will need
to find it via $PYTHONPATH
$ export \
PYTHONPATH=/path/to/where/you/want/bokeep/lib/python2.x/site-packages/:$PYTHONPATH

Test as follows
$ python
>>> import bokeep

The executable binary (bo-keep) will be available in
/path/to/where/you/want/bokeep/bin/

Our setup.py can also run the entire 194 tests (and counting) in our
test suite. (GnuCash with python bindings required) $ python setup.py
test


Copyright (C) 2012  ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
This file is part of Bo-Keep.

Bo-Keep is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Authors: Mark Jenkins <mark@parit.ca>
         Samuel Pauls <samuel@parit.ca>
