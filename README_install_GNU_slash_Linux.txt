Before we install Bo-Keep on GNU/Linux we have to install the required
dependencies PyGTK and ZODB. You'll likely want GnuCash as well for a
real backend plugin.

It is assumed you have a GNU/Linux distribution with a python
interpretor installed. (we've tested the CPython implementation
[http://python.org] versions 2.5 and 2.6, it's possible that we've
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


Debian based distributions are not yet shipping a version of GnuCash
(http://gnucash.org/) 2.4.0 with python bindings enabled, so you have
to build it yourself, which is a PITA due to build dependencies. We're
committed to getting the Debian packaging updated for this right away.

Alternatively you may find
http://wiki.gnucash.org/wiki/GnuCash#Installation to be helpful;
included are instructions for other distros.

So here's the Debian way to get the dependencies (this was tested on
Ubuntu 10.04)
# aptitude install intltool pkg-config libglib2.0-dev guile-1.6-dev \
guile-1.6-slib libgconf2-dev libxml2-dev zlib1g-dev libofx-dev \
libaqbanking-dev libpopt-dev libgtk2.0-dev libgnomeui-dev \
libglade2-dev libgoffice-0.8-dev libwebkit-dev libltdl-dev libdbi0-dev \
slib guile-1.6-slib libfinance-quote-perl libwww-perl libhtml-tree-perl \
libhtml-tableextract-perl libcrypt-ssleay-perl libdate-manip-perl \
python-dev

And on to building the damn thing

# mkdir -p /opt/src/
# cd /opt/src/
# wget \
# http://downloads.sourceforge.net/sourceforge/gnucash/gnucash-2.4.0.tar.bz2
# tar xjf gnucash-2.4.0.tar.bz2
# cd gnucash-2.4.0
# ./configure \
--prefix=/opt/gnucash-2.4.0/ --enable-python-bindings
# make && make install

To use the python bindings, you need to either install GnuCash in a
place like /usr/ or /usr/local where your python interpreter can find
it, or set the PYTHONPATH environmental variable
$ export PYTHONPATH=/opt/gnucash-2.4.0/lib/python2.x/site-packages/:$PYTHONPATH

Test this
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


Copyright (C) 2011  ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
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

 Author: Mark Jenkins <mark@parit.ca>
