Every plugin should have a get_plugin_class function. If your plugin
is a single python module, declare get_plugin_class in that file. If
your plugin is a python package, declare or import get_plugin_class
from your __init__.py.

This function should return a class that represents your plugin. When
a user adds your plugin, BoKeep will instantiate the class returned by
get_plugin_class . 

Your plugin should implement the methods documented in
bokeep.prototype_plugin

>>> import bokeep.prototype_plugin help(bokeep.prototype_plugin)

You can inherit from bokeep.prototype_plugin.PrototypePlugin if you
want a dummy plugin to start with, but you will more or less have to
override all of its methods.


Copyright (C) 2010  ParIT Worker Co-operative, Ltd
<paritinfo@parit.ca> This file is part of Bo-Keep.

Bo-Keep is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your
option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

 Author: Mark Jenkins <mark@parit.ca>
