The trust plugin was developed for Legal Aid Manitoba (http://www.legalaid.mb.ca). The intended use is by a trustee who holds onto money on behalf of a trustor.

There are only two transaction types, Trust Money In (trustee takes money from trustor) and Trust Money Out (trustee pays money out to or for the benifit of the trustor).

There are two parts to the interface, a combo box for selecting the trustor and the amount of money involved as a positive decimal value.

In the trust plugin configuration interface you can define the trustors. Enter a name in the name field and click on the "save" button to add it to the list on the left hand side. The "add" button mearly erases the name field, nothing more.

There is currently a quirk where after returning from the trust plugin configuration interface the new list of trustors isn't available, you have to refresh the gui somehow via navigation, restarting the app, or something.

The trust entries appear in your books with the amounts entered. You'll need to enter a three letter ISO 4217 (http://en.wikipedia.org/wiki/ISO_4217) currency code at the bottom if you're using a Bo-keep backend plugin that requires one. The GnuCash backend plugin requires this -- a complete list of supported ones is available in GnuCash itself.

The current default, CAD is Canadian Dollar (because the original developers are loonie!). For anyone too lazy to lookup the code for US Dollar or Euro, the codes are USD and EUR. (I want a toonie for every end-user who claims to have read this doc and still asks by email or chat about one of those two codes)

Any accounting backend will probably need you to select a Cash and Trust Liability accounts as well. The GnuCash backend brings up a dialog where you have to enter in the account tree path with the parts colon separated like so Liabilities:Held in Trust . The resulting accounting entry is two lines, for trust money in a debit on the cash account [it can actually be any account type]  a credit on the trust liability acccount. (also can be any account type)

With the GnuCash backend, the currency selected must match the currency of the two accounts.

There is also a feature for exporting a text balance report and the zoom in button allows you to see a history per trustor and output a text report from that as well.

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
