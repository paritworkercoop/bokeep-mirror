# timesheet.py Timesheeting
# Copyright (C) 2006-2010 ParIT Worker Co-operative <paritinfo@parit.ca>
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
#            Mark Jenkins <mark@parit.ca>

class Timesheet():
    def __init__(self, sheet_date, hours, memo):
        self.sheet_date = sheet_date
        self.hours = hours
        self.memo = memo
        
    def __str__(self):
        retstr = 'TIMESHEET\n'
        retstr += 'date: ' + str(self.sheet_date) + '\n'
        retstr += 'hours: ' + str(self.hours) + '\n'
        retstr += 'memo: ' + str(self.memo) + '\n'
        return retstr
