# Copyright (C) 2011  ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
#
# This file is part of Bo-Keep.
#
# Bo-Keep is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Authors: Mark Jenkins <mark@parit.ca>

"""Constants used by BoKeep shells

display_module constants are used by shells when they call functions
returned by get_transaction_display_by_mode_hook for displaying transactions.
These constants are used to tell the plugin to display all, some, or none
of thier parts read only, and also provide context such as the transaction
being new or not and if its being viewed by a headless shell.
  TRANSACTION_ALL_EDIT_FIRST_TIME
    - We're editing a transaction that was just created and everything about it
      should be editable
  TRANSACTION_ALL_EDIT_FIRST_TIME_HEADLESS
    - This is like TRANSACTION_ALL_EDIT_FIRST_TIME but only with a
      headless shell involved
  TRANSACTION_ALL_EDIT - Edit all aspects of the transaction
  TRANSACTION_ALL_EDIT_HEADLESS
    - like TRANSACTION_ALL_EDIT only with a headless shell known be in control
  TRANSACTION_WITH_ESSENTIALS_READ_ONLY
    - Allow the transaction to be editted, but essential information that
      shouldn't be touched in a subsequent edit should be left read-only.
      It's up to the plugin to decide what's essential, but a common example
      is when the plugin associates the transaction with some kind of
      entity -- the choice of entity should be deemed essential, and changing
      that after the initial edit should be considered weird.
      For example, the trust plugin has a trustor selection, or a future billing
      plugin a vendor selection
  TRANSACTION_WITH_ESSENTIALS_READ_ONLY_HEADLESS
    - Like TRANSACTION_WITH_ESSENTIALS_READ_ONLY, only with a headless shell
  TRANSACTION_READ_ONLY - Nothing should be edditable, everything read only
  TRANSACTION_READ_ONLY_HEADLESS - like TRANSACTION_READ_ONLY only for a
  headless shell
 

NEW_ATTACH_EDITOR_HOOK_ATTRIBUTE provides string that can be used to check
for the get_transaction_display_by_mode_hook attribute.

GUI_STATE_SUB_DB is the name of the sub database where several shells track
the most recent transaction being displayed
"""


(TRANSACTION_ALL_EDIT_FIRST_TIME,
 TRANSACTION_ALL_EDIT_FIRST_TIME_HEADLESS,
 TRANSACTION_ALL_EDIT,
 TRANSACTION_ALL_EDIT_HEADLESS,
 TRANSACTION_WITH_ESSENTIALS_READ_ONLY,
 TRANSACTION_WITH_ESSENTIALS_READ_ONLY_HEADLESS,
 TRANSACTION_READ_ONLY,
 TRANSACTION_READ_ONLY_HEADLESS) = range(8)

HEADLESS_MODES = (TRANSACTION_ALL_EDIT_FIRST_TIME_HEADLESS,
                  TRANSACTION_ALL_EDIT_HEADLESS,
                  TRANSACTION_WITH_ESSENTIALS_READ_ONLY_HEADLESS,
                  TRANSACTION_READ_ONLY_HEADLESS)

NEW_ATTACH_EDITOR_HOOK_ATTRIBUTE = "get_transaction_display_by_mode_hook"

GUI_STATE_SUB_DB = 'gui_state'
