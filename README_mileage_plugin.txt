The mileage plugin was developed entirely for demonstration purposes. Looking at it is a good place to start if you want to develop your own Bo-Keep plugin.

There is only one transaction type, Mileage provided. There are two parts to the interface, a calendar for selecting a date, and a text entry for entering indicating the distance traveled. Decimal values are allowed. The label says "Distance (km/miles)", but when we look at the configuration interface, you'll see you can actually use whatever units you want.

In the configuration interface you can choose a distance multiplier. The entry in your books will be the distance entered multiplied by this amount; so the meaning is dollars (or pesos or yen or whatever) per distance unit.

Speaking of pesos (MXN), you'll need to enter a three letter ISO 4217 (http://en.wikipedia.org/wiki/ISO_4217) currency code at the bottom if you're using a Bo-keep backend plugin that requires one. The GnuCash backend plugin requires this -- a complete list of supported ones is available in GnuCash itself.

The current default, CAD is Canadian Dollar (because the original developers are loonie!). For anyone too lazy to lookup the code for US Dollar or Euro, the codes are USD and EUR. (I want a toonie for every end-user who claims to have read this doc and still asks by email or chat about one of those two codes)

Any accounting backend will probably need you to select an expense (debit) and credit account as well. The GnuCash backend brings up a dialog where you have to enter in the account tree path with the parts colon separated like so Expenses:Car . The resulting accounting entry is two lines, a debit on the expense (debit) account [it can actually be any account type] equal to the distance times the multiplier, and a credit (same amount) on the credit account.

With the GnuCash backend, the currency selected must match the currency of the two accounts.

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
