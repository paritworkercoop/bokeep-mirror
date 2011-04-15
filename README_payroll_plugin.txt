The payroll code is the oldest in Bo-Keep, going all the way back to
2006. Its origins lie in cdnpayroll by Paul Evans
(http://cdnpayroll.gemlog.ca/), but we rewrote everything by 2007. We
still list Paul Evans as a co-copyright holder in the copyright
headers in bokeep.plugins.payroll.canada only because we've never
asked a lawyer if we could yank em or bothered Paul with a clearance
request.

[Paul Evans has seen our code, was impressed and would be interested
in co-maintaining the calculations, we just need to re-work things to
allow him to keep his interface (user and api) and us keep ours. It
would be cool if the src/bokeep/plugins/canada/ directory could be
shared and nothing more to keep this simple ]

The payroll code benifited from grant funding from Assiniboine Credit
Union (http://assiniboine.mb.ca)

Right now this plugin only supports Manitoba (province), Canada
payrolls, so its only useful to 1/6000 of the world. Adding support
for another Canadian province would be fairly easy. There are generic
payroll classes like Payday, Paystub, and PaystubLine,
PaystubIncomeLine, Employee etc that would be useful for the rest of
the world as well, but these ought to be moved out of
src/bokeep/plugins/canada and into src/bokeep/plugins/ without borking
the zodb database of the real life deployments using this.

Even if you're not in Manitoba, Canada and not in the mood to help us
make this more generic, trying this plugin out is worth your time for
the wow factor, unlike the mileage and trust plugins, this one
delivers a pretty high ratio of backend output per front-end input,
illustrating the true power of Bo-keep, the ability to take simple
user input, add in some domain knowledge and spit out a spiffy,
balanced, multi-entry accounting transaction in a real accounting
program.

The payroll user-interface is shockingly crude and advanced at the
same time. You select a configuration file describing your payroll's
special rules and a data file with the payday data. These files are
actually python code files that you have to edit to make use of the
payroll system!

It would be too exhausting to document even the space of possibilities
for these that we have thought of, so I'll just refer you to
payroll_example_data_files/payday_data.py and
payroll_example_data_files/payroll_configuration.py in the source tree
and bokeep.plugins.payroll.plain_text_payroll .

The paystub_accounting_line_config object from
payroll_configuration.py contains account specifiers for the
accounting backend plugin. The example has these as objects accepted
by the GnuCash backend plugin, a tuple representing a position in the
account tree. Seeing how the payroll code only works for Manitoba,
Canada right now, we've hard coded the currency to CAD -- or not
bothered to add a configurable option... Your GnuCash accounts (as
specified in your payroll config file) have to be in CAD as well.

The config dialog provides some pretty cool payroll data dumping
features.

"Dump Database" dumps your entire payroll database into a comma
separated value format (csv) suitable for reading in a spreadsheet;
and sorted one by date and once by employee at that!

"Dump T4" takes advantage of one of the few known examples of
technological sanity by the Canadian Government, employers can submit
end of year deduction summaries (T4Slip / T4Summary) in an XML format!
And it comes with a schema too!
http://www.cra-arc.gc.ca/esrvc-srvce/rf/menu-eng.html

(If only the feds did that for corporate and personal income tax
returns too instead of the proprietary, secret walled garden they've
been pushing with my few tax dollars.

I'll be really cheesed if some wonk tries to tell us that we can't
include those schema files in the bo-keep source tree due to the
Canadian anachronism of crown copyright. Can an XML schema even be
covered by copyright in Canada?)

You need to import a file like payroll_example_data_files/t4_data.py
to provide other information about employees and the employer beyond
the stuff extracted in the payroll database.

You can validate the result against the schema files using xmllint
$ xmllint --noout \
--schema src/bokeep/plugins/payroll/T4_xml_schema/layout-topologie.xsd \
your_t4s.xml

The third button, "Dump period analysis" allows you to output a CSV
file for analyzing aggregate deductions on a monthly, quarterly, or
annual basis.

We hope that any attempt to put a proper gui as part of the bokeep
payroll plugin will still retain the power of this system without
reverting to binary choice between a new dumb GUI vs the current
interface. One universal design we have in mind is a TreeView that
allows one to drill down through the levels of Payday, Paystub (per
employee), and PaystubLine (per paystub); thus leaving every paystub
line viewable/editable while still efficiently supporting the most
common case of just entering a single hours figure per employee.

The configuration side could be defaulted to something simple like
payroll_example_data_files/payroll_configuration.py has, while also
being user replaceable with user-provided code.  We at ParIT take
advantage of this  for our payroll, we break our hours down into about
10 different categories because about 85% of our income goes into
wages and we use this data to assess our business performance and to
reconfigure our billing rates. We also three unique circumstances for
special deductions that go to the employer that end up in different
accounts.

One of our clients also has their own unique quirks in their payroll
which a code customizable configuration system helps support.

Most other employers have things unique to their payroll as well,
e.g. unions dues, retirement saving plan contributions, company
pensions, commissions, bonuses, stock options, charitable donations,
loss take-backs, and on and on so it really does make sense to keep
this system flexible through a code based configuration to discourage
code forking.

---
Warnings:

You should be advised that the new payroll plugin feature where config files
are auto loaded has some downsides that need to be paid attention to.

If you want to re-enter the data on an old payroll, keep in mind that if you
have a plugin wide config file set that it will be used and you need a
compatible data file. If you've been changing your config file, it may
not be compatible if you're using a data file that had previously worked with
a different, old config file.

Also, when viewing old payrolls, your current new config will be used to
generate the printable paystub, so these may not look like the paystubs
that would of been seen before.

A future version of bo-keep (after 1.0.3) will address this by allowing you
to lock in old payrolls to always use a config file from a specific location;
this will allow you to archive an old configuration and ensure it is continued
to be used on future edits or views of your transactions.

In addition, the safety measures for allowing checksum based checking of
compatible configurations as being developed for the multipage glade plugin
may also be put to use.

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
