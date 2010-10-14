# Copyright (C) 2010  ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
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
# Author: Mark Jenkins <mark@parit.ca>
# ZODB
from persistent import Persistent
import transaction

from bokeep.util import \
    ends_with_commit, FunctionAndDataDrivenStateMachine, \
    state_machine_do_nothing, state_machine_always_true

# possible actions
(NEW, DELETE, FORWARD, BACKWARD, TYPE_CHANGE, BOOK_CHANGE, CLOSE) = \
    range(7)

# tuple indexes for data stored in BoKeepGuiState
(BOOK, TRANS) = range(2)

class BoKeepGuiState(FunctionAndDataDrivenStateMachine):
    NUM_STATES = 5
    (
        # There is no book selected
        NO_BOOK,
        # A temporary state. A book is selected, and we just need to
        # figure out if we should go to NO_TRANSACTIONS or NEW_TRANSACTION
        TMP_GOTO_NO_TRANS_OR_BROWSE,
        # A book is selected, but there are no transactions
        NO_TRANSACTIONS,
        # A new transaction is being editted
        NEW_TRANSACTION,
        # we're looking at an existing transaction
        BROWSING,
        ) = range(NUM_STATES)

    def __init__(self):
        FunctionAndDataDrivenStateMachine.__init__(self,
            data=(None, None), # book (BOOK), transaction_id (TRANS)
            initial_state=BoKeepGuiState.NO_BOOK)
        self.run_until_steady_state()
        assert(self.state == BoKeepGuiState.NO_BOOK)
    
    def get_table(self):
        # possible causes of state change are the actions
        # back
        # forward
        # new
        # delete
        # change type
        # change book
        # close
        
        if hasattr(self, '_v_table_cache'):
            return self._v_table_cache

        STANDARD_BOOK_CHANGE_CLAUSE = \
            (BoKeepGuiState.__make_action_check_function(BOOK_CHANGE),
             BoKeepGuiState.__absorb_new_book,
             BoKeepGuiState.TMP_GOTO_NO_TRANS_OR_BROWSE)

        STANDARD_NEW_TRANSACTION_CLAUSE = \
            (BoKeepGuiState.__make_action_check_function(NEW),
             BoKeepGuiState.__new_transaction_using_current_type,
             BoKeepGuiState.NEW_TRANSACTION)

        # If the delete action occured, unregister the
        # current transaction from the module that created it,
        # remove it from the book, and leave it up to
        # TMP_GOTO_NO_TRANS_OR_BROWSE to see if we're going
        # back to viewing another transaction or looking at none
        STANDARD_DELETE_TRANSACTION_CLAUSE = \
            (BoKeepGuiState.__make_action_check_function(DELETE),
             BoKeepGuiState.__purge_current_transaction,
             BoKeepGuiState.TMP_GOTO_NO_TRANS_OR_BROWSE)

        STANDARD_BACKWARD_CLAUSE = \
            (BoKeepGuiState.__make_action_check_function(BACKWARD),
             BoKeepGuiState.__go_backward,
             BoKeepGuiState.BROWSING)

        self._v_table_cache = (
            # NO_BOOK
            #
            ( STANDARD_BOOK_CHANGE_CLAUSE,
              ), # NO_BOOK
            
            # TMP_GOTO_NO_TRANS_OR_BROWSE
            #
            # check if there is even a book
            ( (BoKeepGuiState.__no_book, state_machine_do_nothing,
               BoKeepGuiState.NO_BOOK),
              # check if there are no transactions in this book
              (BoKeepGuiState.__no_transactions_in_book,
                BoKeepGuiState.__set_transaction_id_to_none,
               BoKeepGuiState.NO_TRANSACTIONS),
              # else, there are transactions in this book, use the
              # latest one and BROWSE to it
              (state_machine_always_true,
               BoKeepGuiState.__use_latest_transaction_in_book,
               BoKeepGuiState.BROWSING),
              ), # TMP_GOTO_NO_TRANS_OR_BROWSE
            
            # NO_TRANSACTIONS
            #
            # if the book changes, we return temporarilly to the
            # TMP_GOTO_NO_TRANS_OR_BROWSE state, which will sort
            # things out and bring
            # us either back to NO_TRANSACTIONS or BROWSING if a new
            # book was selected instead of none
            ( STANDARD_BOOK_CHANGE_CLAUSE,
              # if the new action occured
              # we create a new transaction based on the first
              # available type, register it with its module, and 
              # transition to being in the state of editting it
              # for the first time
              STANDARD_NEW_TRANSACTION_CLAUSE,
              ), # NO_TRANSACTIONS
        
            # NEW_TRANSACTION
            #
            # If the new action occured, we're done the first edit
            # on the current transaction, we start a new first edit
            # on a new transaction of the same type
            ( STANDARD_NEW_TRANSACTION_CLAUSE,
              STANDARD_DELETE_TRANSACTION_CLAUSE,
              # action forward is never possible in this state, so
              # we don't check for it
              #
              # if the back action occured, this current transaction
              # is no longer considered new, just browse whatever came
              # before it
              STANDARD_BACKWARD_CLAUSE,
              # if the transaction type changed, remove the one
              # that's present, and create a new one of the
              # new type for new editing
              (BoKeepGuiState.__make_action_check_function(TYPE_CHANGE),
               BoKeepGuiState.__type_change,
               BoKeepGuiState.NEW_TRANSACTION),
              # if the book has changed, we start all over, this
              # current transaction is no longer in its first edit
              STANDARD_BOOK_CHANGE_CLAUSE,
              # if the book is being closed for access, this original
              # first new edit is done, when we return we're just
              # browsing the same transaction
              (BoKeepGuiState.__make_action_check_function(CLOSE),
               state_machine_do_nothing, BoKeepGuiState.BROWSING),
              ),  # NEW_TRANSACTION
     
            # BROWSING
            ( (BoKeepGuiState.__make_action_check_function(FORWARD),
               BoKeepGuiState.__go_forward,
               BoKeepGuiState.BROWSING),
              STANDARD_BACKWARD_CLAUSE,
              STANDARD_NEW_TRANSACTION_CLAUSE,
              STANDARD_DELETE_TRANSACTION_CLAUSE,
              STANDARD_BOOK_CHANGE_CLAUSE,
              # change type not meaningful when browsing, transactions
              # must stay the same.
              # nothing needs to happen if close action in BROWSING,
              # cause we'll resuming browsing the same thing when reopened
              # again
              ) # BROWSING
            ) # end table
        
        return self._v_table_cache

    # state machine condition functions
    def __no_transactions_in_book(self, next_state):
        return self.data[BOOK].get_transaction_count() == 0

    def __no_book(self, next_state):
        return self.data[BOOK] == None

    @staticmethod
    def __make_action_check_function(action):
        def check_function(self, next_state):
            if hasattr(self, "_v_last_action"):
                result = self._v_last_action == action
                if result:
                    delattr(self, "_v_last_action")
                return result
            else: return False
        return check_function

    # helper functions for the state machine transition functions
    def __get_code_classs_module_for_index(self, index=0):
        return tuple(
            self.data[BOOK].get_iter_of_code_class_module_tripplets(
                ))[index]        

    def __add_transaction_instance_to_book_and_module(self, cls, module):
        new_transaction_instance = cls()
        new_transaction_id = self.data[BOOK].insert_transaction(
            new_transaction_instance)
        module.register_transaction(new_transaction_id,
                                    new_transaction_instance)
        return new_transaction_id

    # state machine transition functions
    def __absorb_new_book(self, next_state):
        return (self._v_action_arg, None)

    def __use_latest_transaction_in_book(self, next_state):
        new_trans_id = self.data[BOOK].get_latest_transaction_id()
        assert(new_trans_id != None)
        return (self.data[BOOK], new_trans_id)

    def __set_transaction_id_to_none(self, next_state):
        return (self.data[BOOK], None)

    def __new_transaction_using_current_type(self, next_state):
        if self.data[TRANS] == None:
            code, cls, module = self.__get_code_classs_module_for_index(0)
        else:
            i, (code, cls, module) = \
                self.data[BOOK].\
                get_index_and_code_class_module_tripplet_for_transaction(
                self.data[TRANS] )
        return (self.data[BOOK], 
                self.__add_transaction_instance_to_book_and_module(
                cls, module))
    
    def __purge_current_transaction(self, next_state):
        (i, (code, cls, module)) = \
            self.data[BOOK].\
            get_index_and_code_class_module_tripplet_for_transaction(
            self.data[TRANS])
        module.remove_transaction(self.data[TRANS])
        self.data[BOOK].remove_transaction(self.data[TRANS])
        return (self.data[BOOK], None)

    def __type_change(self, next_state):
        self.__purge_current_transaction(next_state)
        assert( self._v_action_arg != None )
        code, cls, module = self.__get_code_classs_module_for_index(
            self._v_action_arg)
        return (
            self.data[BOOK], 
            self.__add_transaction_instance_to_book_and_module(
                cls, module) )

    def __go_backward(self, next_state):
        trans_id = self.data[BOOK].get_previous_trans(self.data[TRANS])
        assert(trans_id != None)
        return (self.data[BOOK], trans_id)

    def __go_forward(self, next_state):
        trans_id = self.data[BOOK].get_next_trans(self.data[TRANS])
        assert(trans_id != None)
        return (self.data[BOOK], trans_id)

    # public api for use by mainwindow.py, or any other multi transaction
    # shell

    @ends_with_commit
    def do_action(self, action, arg=None):
        assert( self.action_allowed(action) )
        self._v_action_arg = arg
        self._v_last_action = action
        self.run_until_steady_state()
        delattr(self, '_v_action_arg')

    def action_allowed(self, action):
        assert(self.state != BoKeepGuiState.TMP_GOTO_NO_TRANS_OR_BROWSE)
        if not hasattr(self, '_v_action_allowed_table'):
            self._v_action_allowed_table = {
                NEW : lambda: (
                    self.state != BoKeepGuiState.NO_BOOK and
                    len(tuple(self.data[BOOK].
                        get_iter_of_code_class_module_tripplets())) > 0),
                DELETE: lambda: (
                    self.state != BoKeepGuiState.NO_BOOK and 
                    self.state != BoKeepGuiState.NO_TRANSACTIONS ),
                FORWARD: lambda: (
                    self.state == BoKeepGuiState.BROWSING and 
                    self.data[BOOK].has_next_trans(self.data[TRANS]) ),
                BACKWARD: lambda: (
                    (self.state == BoKeepGuiState.BROWSING or 
                     self.state == BoKeepGuiState.NEW_TRANSACTION) and 
                    self.data[BOOK].has_previous_trans(self.data[TRANS]) ),
                # could ammend this to check if there are even
                # more than one type available
                TYPE_CHANGE: lambda: (
                    self.state == BoKeepGuiState.NEW_TRANSACTION),

                # should change this to only allow a book change when there
                # are more than one, otherwise what's the point, don't
                # give the user illusions...
                BOOK_CHANGE: lambda: True,
                CLOSE: lambda: True,
                }
        if action in self._v_action_allowed_table:
            return self._v_action_allowed_table[action]()
        else:
            raise Exception("action %s is not defined" % action)

    def get_transaction_id(self):
        return self.data[TRANS]

    def get_book(self):
        return self.data[BOOK]
