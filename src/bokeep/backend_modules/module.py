from persistent import Persistent

from bokeep.book_transaction import \
    BoKeepTransactionNotMappableToFinancialTransaction

from bokeep.util import \
    ChangeMessageRecievingThread, EntityChangeManager, entitymod, \
    ends_with_commit, FunctionAndDataDrivenStateMachine, \
    state_machine_do_nothing, state_machine_always_true, \
    StateMachineMinChangeDataStore

import transaction

class BackendChangeManager(EntityChangeManager):
    def __init__(self, running_thread, entity_identifier):
        EntityChangeManager.__init__(self, running_thread, entity_identifier)
        self.transaction_dirty_count = 0

    def increment(self):
        self.transaction_dirty_count += 1
    
    def send_to_zero(self):
        return_value = self.transaction_dirty_count
        self.transaction_dirty_count = 0
        return return_value
 

class BackendChangeThread(ChangeMessageRecievingThread):
    
    @entitymod
    def mark_transaction_dirty(self, change_manager, entity_identifier):
        change_manager.increment()

    def get_entity_from_identifier(self, entity_identifier):
        pass

    def handle_entity_change(self, change_message, entity):
        # change required, only do this if backend is co-operative, if it
        # is locked or something ,imform other that it is still dirty
        # I wonder if we can avoid this...
        count_down = change_message.send_to_zero()
        
        # put representation of entity identified by
        # change_message.entity_identifier, and old backend id
        # to backend, receie returned backenend id and store
        #
        # send count_down back to the backend module dirty db, or nothing

        
def error_in_state_machine_data_is(error_code):
    def error_check_function(state_machine, next_state):
        return state_machine.data.get_value("error_code") == error_code
    return error_check_function

def particular_input_state_machine(input):
    def command_check(state_machine, next_state):
        return state_machine.backend_module.dirty_transaction_set[
            state_machine.data.get_value('front_end_id')] == input
    return command_check


class BackendDataStateMachine(FunctionAndDataDrivenStateMachine):
    def __init__(self, init_data, backend_module):
        FunctionAndDataDrivenStateMachine.__init__(
            self,
            initial_state=BackendDataStateMachine.NO_BACKEND_EXIST,
            data=init_data)
        self.backend_module = backend_module

    @classmethod
    def get_table(cls):
        return cls.__backend_rule_table

    def __remove_transaction_state_machine(state_machine, next_state):
        """Removes the reference
        to the state machine from __front_end_to_back
        """
        # this function doesn't make sense to call when the error flag is up
        assert(state_machine.data.get_value('error_code') ==
               BackendDataStateMachine.ERROR_NONE)

        # we shouldn't remove the state machine until there are no backend
        # transactions
        assert(len(state_machine.data.get_value(
                    'backend_ids_to_fin_trans')) == 0)

        state_machine.backend_module.front_end_to_back_del(
            state_machine.data.get_value('front_end_id') )

        return state_machine.data # no changes


    def __create_backend_transaction_state_machine(state_machine, next_state):
        # this doesn't make any sense if there are backend ids in existence
        assert( len(state_machine.data.get_value(
                    'backend_ids_to_fin_trans')) == 0 )
        # nor should there be errors
        assert( state_machine.data.get_value('error_code') ==
                BackendDataStateMachine.ERROR_NONE )
        
        backend_ids_to_fin_trans = state_machine.data.get_value(
            'backend_ids_to_fin_trans')
        bo_keep_trans = state_machine.data.get_value('bo_keep_trans')
        error_code = state_machine.data.get_value('error_code')
        error_string = state_machine.data.get_value('error_string')
        old_backend_ids_to_fin_trans = backend_ids_to_fin_trans.copy()
        try:
            fin_trans_list = list(bo_keep_trans.get_financial_transactions())
        except BoKeepTransactionNotMappableToFinancialTransaction, e:
            error_code = BackendDataStateMachine.ERROR_OTHER
            error_string = e.message
        else:
            try:
                for fin_trans in fin_trans_list:
                    new_backend_id = state_machine.backend_module.\
                        create_backend_transaction(fin_trans)
                    backend_ids_to_fin_trans[new_backend_id] = fin_trans
                    
            except BoKeepBackendException, e:
                error_code = BackendDataStateMachine.ERROR_OTHER
                error_string = e.message

        return state_machine.data.duplicate_and_change(
            backend_ids_to_fin_trans=backend_ids_to_fin_trans,
            old_backend_ids_to_fin_trans=old_backend_ids_to_fin_trans,
            error_code=error_code,
            error_string=error_string,
            )

    def __clear_error_flag_and_msg_state_machine(state_machine, next_state):
        return state_machine.data.duplicate_and_change(
            error_code=BackendDataStateMachine.ERROR_NONE,
            error_string=None)

    def __in_dirty_set_state_machine(state_machine, next_state):
        return state_machine.data.get_value('front_end_id') in \
            state_machine.backend_module.dirty_transaction_set

    def __backend_data_verify_state_machine(state_machine, next_state):
        # should not be errors
        error_code = state_machine.data.get_value('error_code') 
        error_string = state_machine.data.get_value('error_string')
        assert( error_code == BackendDataStateMachine.ERROR_NONE )
        backend_ids_to_fin_trans = \
            state_machine.data.get_value('backend_ids_to_fin_trans')
        for backend_id, fin_trans in backend_ids_to_fin_trans.iteritems():
            try:
                if not state_machine.backend_module.verify_backend_transaction(
                    backend_id, fin_trans):
                    error_code = BackendDataStateMachine.ERROR_VERIFY_FAILED
                    break # for loop
            except BoKeepBackendException, e:
                error_code = BackendDataStateMachine.ERROR_OTHER
                error_string = e.message
                break # for loop

        return state_machine.data.duplicate_and_change(
            error_code=error_code,
            error_string=error_string)

    def __record_reason_for_reset_state_machine(state_machine, next_state):
        return state_machine.data.duplicate_and_change(
            error_code=BackendDataStateMachine.ERROR_OTHER,
            error_string=state_machine.backend_module.get_reason_for_reset() )

    def __remove_backend_transactions_state_machine(state_machine, next_state):
        """Removes any backend transactions listed in the state machine data

        Any backend transactions not removed remain in the list, and the error
        flag is set if this happens
        """
        # this function doesn't make sense to call when the error flag is up
        assert(state_machine.data.get_value('error_code') ==
               BackendDataStateMachine.ERROR_NONE)
        backend_ids_to_fin_trans = \
            state_machine.data.get_value('backend_ids_to_fin_trans')
        error_code = state_machine.data.get_value('error_code')
        error_string = state_machine.data.get_value('error_string')

        removed_backend_ids = set()
        old_backend_ids_to_fin_trans = backend_ids_to_fin_trans.copy()
        try:
            for backend_id in backend_ids_to_fin_trans.iterkeys():
                state_machine.backend_module.remove_backend_transaction(
                    backend_id)
                removed_backend_ids.add(backend_id)
        except BoKeepBackendException, e:
            error_code = BackendDataStateMachine.ERROR_CAN_NOT_REMOVE
            error_string = e.message
        for backend_id in removed_backend_ids:
            del backend_ids_to_fin_trans[backend_id]

        return state_machine.data.duplicate_and_change(
            backend_ids_to_fin_trans=backend_ids_to_fin_trans,
            old_backend_ids_to_fin_trans=old_backend_ids_to_fin_trans,
            error_code=error_code,
            error_string=error_string )



    # state machine inputs
    # keep these syncronized with MACHINE_INPUT_STRINGS
    (BACKEND_RECREATE, BACKEND_VERIFICATION_REQUESTED,
     BACKEND_LEAVE_ALONE_REQUESTED, BACKEND_BLOWOUT_REQUESTED,
     BACKEND_SAFE_REMOVE_REQUESTED, LAST_ACT_NONE, LAST_ACT_SAVE,
     LAST_ACT_RESET) = range(8)
    MACHINE_INPUT_STRINGS = [
        "The backend transaction has been marked dirty for re-creation", #0
        "The backend transaction has been marked for a verify", #1
        "A request as been made to hold the backend transaction", #2
        "A held backend transaction is being removed, despite possibly "
        "not matching the frontend", #3
        "A request has been made to remove the transaction", #4
        "machine input nothing",
        "machine input, save just happended",
        "machine input, reset"
        ]

    # error types for a backend state machine
    # keep these syncronized with ERROR_TYPE_STRINGS
    (ERROR_CAN_NOT_REMOVE, ERROR_VERIFY_FAILED,
     ERROR_OTHER, ERROR_NONE) = range(4)
    ERROR_TYPE_STRINGS = [
        "couldn't remove a transaction from backend", #0
        "a transaction did not match the version in the backend during "
        "verify", #1
        "other type of error", #2
        "no error", #3
        ]

    # These are the states a transaction can be in the backend
    #
    # Important, if you're adding new states, add them at the BOTTOM!
    # because these integers are being persisted!
    #
     # backend transactions do not yet exist
    (NO_BACKEND_EXIST,  # 0
     # an attempt was made to create backend transaction
     BACKEND_CREATION_TRIED, # 1
     # an attempt was made to create a backend transaction, but it never
     # made it, and we don't want to muck with it again until there is a
     # save
     BACKEND_ERROR_WAIT_SAVE, # 2
     # an attempt was made to create a backend transaction, but it never
     # made it
     BACKEND_ERROR, # 3
     # The backend is in sync with the front end, stay in this state
     # until a transaction is marked as dirty
     BACKEND_SYNCED, # 4
     # The backend is out of sync, and will soon be updated
     BACKEND_OUT_OF_SYNC, # 5
     # despite past errors, a new attempt is ready to be be made made to
     # synchronize
     BACKEND_ERROR_TRY_AGAIN, # 6
     # we just forgot past errors, ready for regeneration steps
     BACKEND_ERROR_FORGOTON_TRY_AGAIN, # 7
     # preparing to remove old backend transactions, verification
     # just took place on the way here
     BACKEND_OLD_TO_BE_REMOVED, # 8
     # verification was just requested
     BACKEND_VERIFY_REQUESTED, # 9
     # its been verified, the backend is out of sync, a state we
     # should stay in until explicit user intervention
     #
     # should we consider haiving two different states?,
     # verified bad that was triggered by a removal request (explicit or
     # implicit in regular dirty), and
     # verified bad that was triggered by a verification request
     # Right now, everything is treated like the former, meaning that
     # a verification request could fail, later pass, and result in
     # a full out removal and recreation..., this would kind of suck
     # if removal wasn't possible (due to something like reconcilation),
     # but verification was possible, and all the end user wanted to
     # begin with was a verification...
     # FIXME, differnet comment for each
     BACKEND_HELD_WAIT_SAVE, # 10
     BACKEND_HELD, # 11

     ) = range(11+1)

    # for each state, it is noted if the state is transient (always leads to
    # another state), or non-transient (can lead back to itself and stop the
    # state to state iteration)

    __backend_rule_table = (
        # Rules for state NO_BACKEND_EXIST [0]
        #
        # This is a non-transient state
        ( (error_in_state_machine_data_is(
                    ERROR_CAN_NOT_REMOVE),
           state_machine_do_nothing,
           BACKEND_ERROR_WAIT_SAVE ),

          (particular_input_state_machine(LAST_ACT_RESET),
           state_machine_do_nothing, BACKEND_ERROR_TRY_AGAIN),

          # If a transaction is marked for removal but is in this state
          # all we have to do is remove the state machine
          # next state won't matter
          # if removal has been requested, its easy, we just
          # get rid of the state machine seeing how there are
          # no backend transactions
          (particular_input_state_machine(
                    BACKEND_SAFE_REMOVE_REQUESTED),
           __remove_transaction_state_machine,
           NO_BACKEND_EXIST ),
          # if a forced remove was requested, it must of been sucessful
          # if we got this far, just get rid of the state machine now
          # seeing how we've succeeded
          (particular_input_state_machine(
                    BACKEND_BLOWOUT_REQUESTED),
           __remove_transaction_state_machine,
           NO_BACKEND_EXIST ),
          # if a hold has been requested, its easy, we just
          # go into the hold state
          (particular_input_state_machine(
                    BACKEND_LEAVE_ALONE_REQUESTED),
           state_machine_do_nothing,
           BACKEND_HELD),
          
          # Otherwise, always move to NO_BACKEND_TRIED and try to
          # create the backend transaction
          (state_machine_always_true,
           __create_backend_transaction_state_machine,
           BACKEND_CREATION_TRIED),
          ), # end rules for state NO_BACKEND_EXIST
        
        # Rules for state BACKEND_CREATION_TRIED [1]
        #
        # This is a non-transient state 
        #
        # If there was an error when attempting to create the
        # backend transaction, go to the error state
        ( (error_in_state_machine_data_is(ERROR_OTHER),
           state_machine_do_nothing,
           BACKEND_ERROR_WAIT_SAVE),
          # no need to test for other error codes
          
          # If the transaction was created in the backend, but
          # lost because a save couldn't take place, we'll just
          # have to try again
          (particular_input_state_machine(LAST_ACT_RESET),
           state_machine_do_nothing,
           BACKEND_ERROR_TRY_AGAIN),
          # Otherwise we're just waiting for the save to work out
          (particular_input_state_machine(LAST_ACT_SAVE),
           state_machine_do_nothing, BACKEND_SYNCED),
          ), # end rules for state BACKEND_CREATION_TRIED
        
        # Rules for state BACKEND_ERROR_WAIT_SAVE [2]
        # no big deal if save never happned and we lost it...,
        # just try again
        ( (particular_input_state_machine(LAST_ACT_RESET),
           __clear_error_flag_and_msg_state_machine,
           BACKEND_ERROR_TRY_AGAIN),
          # otherwise we wait until there is a save
          (particular_input_state_machine(LAST_ACT_SAVE),
           state_machine_do_nothing, BACKEND_ERROR),
          ), # end rules for state BACKEND_ERROR_WAIT_SAVE
        
        # rules for BACKEND_ERROR [3]
        # As long as the last thing that happened was a save,
        # we stay here
        # thus non-transient state
        ( (particular_input_state_machine(LAST_ACT_SAVE),
           state_machine_do_nothing, BACKEND_ERROR),
          
          # Now we can move on and try again to commit..
          (state_machine_always_true,
           __clear_error_flag_and_msg_state_machine,
           BACKEND_ERROR_TRY_AGAIN),
          ), # end rules for state BACKEND_ERROR
        
        # Rules for state BACKEND_SYNCED [4]
        # hold up if save just happened
        # non-transient state
        ( (particular_input_state_machine(LAST_ACT_SAVE),
           state_machine_do_nothing, BACKEND_SYNCED),
          # check if dirty in dirty_transaction_set, if so,
          # set the dirty flag in the state machine
          (__in_dirty_set_state_machine,
           state_machine_do_nothing, BACKEND_OUT_OF_SYNC),
          ), # end rules for state BACKEND_SYNCED
        
        # Rules for state BACKEND_OUT_OF_SYNC [5]
        # if a reset brought us here, hold on
        # non-transient state
        ( (particular_input_state_machine(LAST_ACT_RESET),
           state_machine_do_nothing,
           BACKEND_OUT_OF_SYNC),
          # if a verification was requested, do it
          (particular_input_state_machine(
                    BACKEND_VERIFICATION_REQUESTED),
           __backend_data_verify_state_machine,
           BACKEND_VERIFY_REQUESTED),
          # if forced consideration of being out of sync, do it
          (particular_input_state_machine(
                    BACKEND_LEAVE_ALONE_REQUESTED),
           state_machine_do_nothing, BACKEND_HELD),
          # otherwise, we're doing a verify followed by a remove
          # always check if backend data has changed
          (state_machine_always_true,
           __backend_data_verify_state_machine,
           BACKEND_OLD_TO_BE_REMOVED),
          ), # end rules for state BACKEND_OUT_OF_SYNC
        
        # Rules for state BACKEND_ERROR_TRY_AGAIN [6]
        #
        # If we got here because of a reset, just wait in this
        # state and record the reason
        # non-transient state
        ( (particular_input_state_machine(LAST_ACT_RESET),
           __record_reason_for_reset_state_machine,
           BACKEND_ERROR_TRY_AGAIN),
          # otherwise we are ready to try again, the first step
          # being data verification prior to removing anything
          # sitting around in the backend
          (state_machine_always_true,
           __clear_error_flag_and_msg_state_machine,
           BACKEND_ERROR_FORGOTON_TRY_AGAIN),
          ), # end rules for state BACKEND_ERROR_TRY_AGAIN
        
        # Rules for state BACKEND_ERROR_FORGOTON_TRY_AGAIN [7]
        # transient state
        ( (particular_input_state_machine(
                    BACKEND_SAFE_REMOVE_REQUESTED),
           state_machine_do_nothing, BACKEND_VERIFY_REQUESTED ),
          (state_machine_always_true,
           __backend_data_verify_state_machine,
           BACKEND_OLD_TO_BE_REMOVED),
          ), # end rules for state BACKEND_ERROR_FORGOTON_TRY_AGAIN
        
        # Rules for state BACKEND_OLD_TO_BE_REMOVED [8]
        # if the verify failed, we're not going to do removal!
        # transient state
        ( (error_in_state_machine_data_is(
                    ERROR_VERIFY_FAILED),
           state_machine_do_nothing, BACKEND_HELD_WAIT_SAVE),
          (error_in_state_machine_data_is(ERROR_OTHER),
           state_machine_do_nothing, BACKEND_ERROR_WAIT_SAVE),
          # is this really fair if we got here from
          # BACKEND_SYNCED->BACKEND_OUT_OF_SYNC, if there was
          # never an error and just a reset, what's the big deal?
          # why go into an error try again state and not just
          # back to BACKEND_OUT_OF_SYNC?, perhaps there should be a
          # separate path...
          #
          # or maybe this is a good idea, the reason for the reset
          # can end up getting recorded, which may be of interest..
          (particular_input_state_machine(LAST_ACT_RESET),
           state_machine_do_nothing, BACKEND_ERROR_TRY_AGAIN),
          (state_machine_always_true,
           __remove_backend_transactions_state_machine,
           NO_BACKEND_EXIST),
          ), # end rules for state BACKEND_OLD_TO_BE_REMOVED
        
        # Rules for BACKEND_VERIFY_REQUESTED [9]
        # non-transient state
        ( (error_in_state_machine_data_is(
                    ERROR_VERIFY_FAILED),
           state_machine_do_nothing, BACKEND_HELD_WAIT_SAVE),
          (error_in_state_machine_data_is(ERROR_OTHER),
           state_machine_do_nothing, BACKEND_ERROR_WAIT_SAVE),
          (particular_input_state_machine(LAST_ACT_RESET),
           state_machine_do_nothing, BACKEND_OUT_OF_SYNC),
          # if verification was requested, we now know it was a
          # success, so just wait here until the save, after which
          # we can expect that we'll be allowed to advance, and
          # then removed from the dirty set
          (particular_input_state_machine(
                    BACKEND_VERIFICATION_REQUESTED),
           state_machine_do_nothing,
           BACKEND_VERIFY_REQUESTED),
          # its all good
          (state_machine_always_true,
           state_machine_do_nothing, BACKEND_SYNCED),
          ), # end rules for state BACKEND_VERIFY_REQUESTED
        
        # Rules for BACKEND_HELD_WAIT_SAVE [10]
        # non-transient state
        ( (particular_input_state_machine(LAST_ACT_SAVE),
           state_machine_do_nothing, BACKEND_HELD),
          (particular_input_state_machine(LAST_ACT_RESET),
           state_machine_do_nothing, BACKEND_HELD),
          ), # end rules for BACKEND_HELD_WAIT_SAVE
        
        # Rules for BACKEND_HELD [11]
        # non-transient state
        ( (particular_input_state_machine(
                    BACKEND_VERIFICATION_REQUESTED),
           __backend_data_verify_state_machine,
           BACKEND_VERIFY_REQUESTED),
          (particular_input_state_machine(
                    BACKEND_BLOWOUT_REQUESTED),
           __clear_error_flag_and_msg_state_machine,
           BACKEND_OLD_TO_BE_REMOVED),
          ), # end rules for BACKEND_HELD
        
        ) # end state list
        

class BackendModule(Persistent):
    """Illustrates the Bo-Keep backend module API

    A Bo-Keep backend module does not need to be a subclass of
    bokeep.backend_modules.module.BackendModule, but it must implement the
    following functions shown here:
    mark_transaction_dirty, mark_transaction_for_removal,
    mark_transaction_for_verification, mark_transaction_for_hold,
    mark_transaction_for_forced_remove, transaction_is_clean,
    reason_transaction_is_dirty, flush_backend, close
    update_trans_flush_check_and_close, 
    remove_trans_flush_check_and_close,
    verify_trans_and_close, setattr
    
    Many backend modules are easier to implement if you do choose to
    subclass BackendModule, and just implemnt functions such as 
    create_backend_transaction, remove_backend_transaction, can_write, save,
    close, and setattr.

    update_trans_flush_check_and_close, remove_trans_flush_check_and_close,
    and verify_trans_and_close are implemented entirly in terms of
    mark_transaction_dirty, mark_transaction_for_removal,
    mark_transaction_for_verification, flush_backend, transaction_is_clean,
    and close, functions you have to implement anyway, so that alone makes
    inheriting worthwhile.

    All backend modules should subclass persistent.Persistent (from zopedb),
    and dilegenly set self._p_changed where appropriate. 

    Bo-Keep backend modules are not expected to be thread-safe.

    A Bo-Keep backend module translates a Bo-Keep transaction (frontend) into
    some other form of data storage, a backend. This raises many of the
    clasical syncrhonization problems of trying to keep data in two places --
    there are potential issues such as changes being made directly to the
    backend system elsewhere, the backend being temporarilly unavailable,
    and the possibility of Bo-Keep making changes in the backend and
    not having the opportunity to record they were made. 

    Bo-Keep's approach to these complexities is to generally assume that
    an already successfuly created backend transaction hasn't been alterered.
    A backend transaction is considered to be "in-sync" with respect to the
    front end ("clean") unless bo-keep has been told that it might be
    "out of sync" with the front end or "dirty".

    If bo-keep is informed that a particular transaction is out of date,
    is is considered "dirty" until the backend has been syncrhonized with the
    front end again. If bo-keep is informed that a particular transaction no
    longer exists, this also makes it dirty. Bo-Keep may also request
    that a particular transaction be checked for consistency with the backend,
    until this check is completed the dirty status remains.

    to sumarize --
    clean means it is believed the front and back ends are in sync
    (but not activly verified)

    dirty means it is believed the front and back ends are possibly
    out of sync                      

    The bo-keep transaction (front end) should always be considered the
    authoritative data source. You should never intentionally alter backend
    data directly. Think of Bo-Keep as the master data source, and the backend
    as the slave data source. Where possible, you should take advantage of
    features in the underlying backend storage system that allow you to
    prevent changes to bo-keep backend transactions by sources other than
    bo-keep; or at least "mark" that data as belonging to bo-keep an make
    application logic in other systems respect that.

    That being said, backends do have a tendency to get modified by people
    not following the rules (or lax enformement of them),
    which is why requests for a consistency check can be made. In addition,
    if a backend transaction is being removed or replaced, a consistency check
    is automatically performed. If an inconsistency is found, bo-keep will
    not remove the underlying backend transaction. Manual intervention is
    required at that point to determine which side wins out.

    Another consideration in the Bo-keep backend design is the fact that
    some backends can be pretty slow when they read/write data out. This is
    why Bo-keep requires backend callers to first mark all the transactions
    that need to be changed or verified, and then call flush_backend()
    so that they are all possibly handled at the same time.

    update_trans_flush_check_and_close, remove_trans_flush_check_and_close,
    and verify_trans_and_close are convience functions that allow you to combine
    a request for change, flush_backend(), and close() together.

    You should expect close to be called anytime. Also, the other functions
    should still operate after a call to close, they are expected to
    re-aquire any resources required. close should be the last backend module
    function to be called.
    """

         
    def __init__(self):
        Persistent.__init__(self)
        # mapping of front end transaction identifiers to
        # backend transaction state machines
        #
        # perhaps this should be volitile?
        self.__front_end_to_back = {}

        # mapping of front end transaction identifiers to an input
        # for that transaction's state machine
        self.dirty_transaction_set = {}
        # set of front end transaction identified that are dirty, but
        # but are considered impossible to syncronize and are thus being
        # held instead of subjected to failed attempt after failed
        # attempt to syncrhonize
        self.held_transaction_set = set()

        # invarient, an active transaction identifier is always found in
        # the keys of __front_end_to_back, and may be in the keys of
        # self.dirty_transaction_set or contained in self.held_transaction_set
        # but never both
        # self.__transaction_invarient(trans_id) allows this last part
        # to be checked

    # START MANDATORY BO-KEEP BACKEND MODULE API
        
    @ends_with_commit
    def mark_transaction_dirty(self, trans_id, transaction):
        """Indicate a bo-keep transaction is not up to date in the backend.

        This doesn't trigger the backend update itself to occure, that only
        happens when flush_backend is called
 
        trans_id -- Bo-keep identifier for the transaction
        transaction -- The actual bo-keep transaction
        """
        self.__transaction_invarient(trans_id)
        self.__raise_if_held_state(trans_id)

        # if the transaction is currently held, remove it because we're going
        # to give it another chance to be resynced...
        self.__remove_trans_id_from_held_set_if_there(trans_id)
        self.dirty_transaction_set[trans_id] = \
            BackendDataStateMachine.BACKEND_RECREATE
        self.__transaction_invarient(trans_id)

        # right now, we don't support the underlying transaction object
        # becoming a different one...
        #
        # this shouldn't be too hard to fix... or maybe we shouldn't care..
        # TODO: think about it
        if trans_id in self.__front_end_to_back:
            if self.__front_end_to_back[trans_id]. \
                    data.get_value('bo_keep_trans') != transaction:
                   raise BoKeepBackendException(
                       "If you mark an existing transaction dirty you "
                       "must provide the original transaction id and "
                       "transactrion")
        else:
            self.__front_end_to_back[trans_id] = \
                self.__create_new_state_machine(trans_id, transaction)
        self._p_changed = True

    @ends_with_commit
    def mark_transaction_for_removal(self, trans_id):
        """Indicate a bo-keep transaction should be removed from the backend

        This doesn't trigger the backend to immediately do the removal, that
        only happens when flush_backend is called

        trans_id -- Bo-Keep transaction id
        """
        self.__transaction_invarient(trans_id)
        if trans_id not in self.__front_end_to_back:
            raise BoKeepBackendException("%s not a valid transaction id"
                                         % trans_id)
        self.__raise_if_held_state(trans_id)
        self.dirty_transaction_set[trans_id] = \
            BackendDataStateMachine.BACKEND_SAFE_REMOVE_REQUESTED
        self.__transaction_invarient(trans_id)
        self._p_changed = True
    
    @ends_with_commit
    def mark_transaction_for_verification(self, trans_id):
        """Indicate a bo-keep transaction should be compared against the backend

        This exists because there's always the chance of the backend being
        changed by evil forces, so a system administrator might want to
        check if bo-keep's database is out of sync with the backend

        Marking the transaction for verification doesn't cause it to happen
        right away, the verification is only done during the call to
        flush_backend . After that has taken place, you can check if the
        transaction is now considered dirty or not by calling
        transaction_is_clean . If you find it isn't clean, you can call
        reason_transaction_is_dirty to find out why.
        """
        self.__transaction_invarient(trans_id)

        if trans_id in self.dirty_transaction_set and \
                self.dirty_transaction_set[trans_id] != \
                BackendDataStateMachine.BACKEND_VERIFICATION_REQUESTED:
            raise BoKeepBackendException(
                "You can't request verification on a transaction with changes "
                "or being deleted, call mark_transaction_for_verification() "
                "again after flush_backend deals with those changes" )

        if trans_id not in self.__front_end_to_back:
            raise BoKeepBackendException(
                "you can't request verification on a transaction "
                "that has never been doesn't exist.")
        
        self.__remove_trans_id_from_held_set_if_there(trans_id)
        self.dirty_transaction_set[trans_id] = \
            BackendDataStateMachine.BACKEND_VERIFICATION_REQUESTED
        self._p_changed = True

    def mark_transaction_for_hold(self, trans_id):
        self.__transaction_invarient(trans_id)

        if trans_id not in self.__front_end_to_back:
            raise BoKeepBackendException(
                "you can't request a hold a transaction that hasn't even "
                "appeared yet, mark it as dirty, do flush, *THEN* place "
                "the hold request and flush again")
        
        # don't bother if the transaction is already held..
        if not self.__trans_id_in_held_set(trans_id):
            self.dirty_transaction_set[trans_id] = \
                BackendDataStateMachine.BACKEND_LEAVE_ALONE_REQUESTED
            self._p_changed = True

    def mark_transaction_for_forced_remove(self, trans_id):
        """Will ensure a transaction in a held state is removed despite
        being out of sync. If you want to try recreating the transaction
        again after, you have to flush_backend() after this, and then call
        mark_transaction_as_dirty and flush_backend()
        """
        self.__transaction_invarient(trans_id)
        if self.__trans_id_in_held_set(trans_id):
            self.__transaction_invarient(trans_id)
            self.__remove_trans_id_from_held_set_if_there(trans_id)
            self.dirty_transaction_set[trans_id] = \
                BackendDataStateMachine.BACKEND_BLOWOUT_REQUESTED
            self.__transaction_invarient(trans_id)
            self._p_changed = True
        else:
            raise BoKeepBackendException(
                "You can't request a forced remove unless a transaction has "
                "already been shown to be in a bad enough state to go into "
                "a hold. Call mark_transaction_dirty, "
                "mark_transaction_for_removal, or "
                "mark_transaction_for_verification, followed by flush_backend "
                "first.")
            

    def transaction_is_clean(self, trans_id):
        """Returns True if a transaction is not dirty, marked for removal,
        or in any other state than the normal one
        """
        if trans_id not in self.__front_end_to_back:
            raise BoKeepBackendException(
                "A transaction must exist to be considered clean")
        
        self.__transaction_invarient(trans_id)
        result = (trans_id not in self.dirty_transaction_set) and \
            (not self.__trans_id_in_held_set(trans_id))
        if result:
            # there shouldn't be any error flags if above conditions hold..
            assert( self.__front_end_to_back[trans_id].data.get_value(
                    'error_code') == BackendDataStateMachine.ERROR_NONE )
        return result

    def reason_transaction_is_dirty(self, trans_id):
        """Returns a string that describes why a particular transaction is still
        dirty, marked for removal, or in any other non-clean / non-normal state.

        You should only call this if you've first called transaction_is_clean(),
        otherwise it isn't meaningful and will give you an exception

        You will get an error if you call this when trans_id doesn't
        exist
        """
        error_code = self.__front_end_to_back[trans_id].data.get_value(
            'error_code')
        clean_status = self.transaction_is_clean(trans_id)
        # its possible to not be clean without an error,
        # to not be clean with an error, and it is
        # possible to be clean without an error
        # but it isn't possible to be clean and have an error
        assert( not (clean_status and error_code !=
                     BackendDataStateMachine.ERROR_NONE ) )
        if error_code == BackendDataStateMachine.ERROR_NONE:
            if clean_status:
                raise BoKeepBackendException("the transaction isn't dirty")
            if trans_id in self.dirty_transaction_set:
                trans_dirty_reason = self.dirty_transaction_set[trans_id]
            else:
                assert(self.__trans_id_in_held_set(trans_id) )
                trans_dirty_reason = \
                    BackendDataStateMachine.BACKEND_LEAVE_ALONE_REQUESTED
            return 'reason dirty: %s, %s' % (
                trans_dirty_reason,
                BackendDataStateMachine.MACHINE_INPUT_STRINGS[
                    trans_dirty_reason] )
        else:
            return 'error code: %s--%s, %s' % (
                error_code,
                BackendDataStateMachine.ERROR_TYPE_STRINGS[error_code],
                self.__front_end_to_back[trans_id].data.get_value(
                    'error_string') )
    
    def flush_backend(self):
        """Take all transactions that are dirty or marked for removal
        writes them out / removes them out if possible.

        When this is done, it does a zopedb transaction commit, if you're
        sharing a zopedb thread with this you'll want to be sure your data
        is in a state you're comfortable having commited
        """
        # if we can write to the backend
        if self.can_write():
            dirty_set_copy = self.dirty_transaction_set.copy()
            try:
                self.__advance_all_dirty_transaction_state_machine()
                self._p_changed = True
                transaction.get().commit()

                # save, and let all dirty transactions change thier state
                # with the knowledge that a save just took place
                try:
                    self.save()
                except BoKeepBackendException, e:
                    # call close, which also triggers backend_reset_occured()
                    self.close('called close() because save failed ' + \
                                   e.message) 
                else:
                    for dirty_trans_id in self.dirty_transaction_set.iterkeys():
                        self.dirty_transaction_set[dirty_trans_id] = \
                            BackendDataStateMachine.LAST_ACT_SAVE
                    self.__advance_all_dirty_transaction_state_machine()

            except BoKeepBackendResetException, reset_except:
                if reset_except.message != '':
                    self.__set_all_transactions_to_reset_and_advance(
                        reset_except.message)
                else:
                    self.__set_all_transactions_to_reset_and_advance()
            else:
                self._p_changed = True
                transaction.get().commit()

            self.__update_dirty_and_held_transaction_sets()
            for trans_id, original_input_value in \
                    dirty_set_copy.iteritems():
                if trans_id in self.dirty_transaction_set:
                    self.dirty_transaction_set[trans_id] = \
                        original_input_value
            self._p_changed = True
            transaction.get().commit()

    def close(self, close_reason='reset because close() was called'):
        """Instructs the module to release any resources being used to
        access the backend.

        This should be called when done with a backend module.

        Any other calls made since the last call to flush_backend may be lost()
        """
        self.__set_all_transactions_to_reset_and_advance(close_reason)

    @ends_with_commit
    def update_trans_flush_check_and_close(self, trans_id, transaction):
        """When this is done, it does a zopedb transaction commit, if you're
        sharing a zopedb thread with this you'll want to be sure your data
        is in a state you're comfortable having commited
        """
        self.mark_transaction_dirty(trans_id, transaction)
        self.flush_backend()
        is_clean = self.transaction_is_clean(trans_id)
        self.close()
        return is_clean
    
    @ends_with_commit
    def remove_trans_flush_check_and_close(self, trans_id):
        """When this is done, it does a zopedb transaction commit, if you're
        sharing a zopedb thread with this you'll want to be sure your data
        is in a state you're comfortable having commited
        """
        self.mark_transaction_for_removal(trans_id)
        self.flush_backend()
        is_gone = trans_id not in self.dirty_transaction_set
        self.close()
        return is_gone

    @ends_with_commit
    def verify_trans_and_close(self, trans_id):
        """When this is done, it does a zopedb transaction commit, if you're
        sharing a zopedb thread with this you'll want to be sure your data
        is in a state you're comfortable having commited
        """
        self.mark_transaction_for_verification(trans_id)
        self.flush_backend()
        is_clean = self.transaction_is_clean(trans_id)
        self.close()
        return is_clean

    # TODO convience functions for hold and forced remove

    @ends_with_commit
    def setattr(self, attr, value):
        """When this is done, it does a zopedb transaction commit, if you're
        sharing a zopedb thread with this you'll want to be sure your data
        is in a state you're comfortable having commited
        """
        setattr(self, attr, value)
        self.flush_backend()

    # END MANDATORY BO-KEEP BACKEND MODULE API

    def front_end_to_back_del(self, key):
        del self.__front_end_to_back[key]

    def get_reason_for_reset(self):
        return self.__reason_for_reset

    def __remove_trans_id_from_held_set_if_there(self, trans_id):
        if self.__trans_id_in_held_set(trans_id):
            self.held_transaction_set.remove(trans_id)
        self._p_changed = True

    def __trans_id_in_held_set(self, trans_id):
        return trans_id in self.held_transaction_set

    def __transaction_invarient(self, trans_id):
        assert( not (trans_id in self.held_transaction_set and
                     trans_id in self.dirty_transaction_set ) )

    def __advance_all_dirty_transaction_state_machine(self):
        # advance all diryt state machines
        for key in self.dirty_transaction_set.iterkeys():
            # but only ones that still exist..
            if key in self.__front_end_to_back:
                self.__front_end_to_back[key].run_until_steady_state()

    def __set_all_transactions_to_reset_and_advance(
        self, reset_reason="reset"):
        self.__reason_for_reset = reset_reason
        for dirty_trans_id in self.dirty_transaction_set.iterkeys():
            self.dirty_transaction_set[dirty_trans_id] = \
                BackendDataStateMachine.LAST_ACT_RESET
        self.__advance_all_dirty_transaction_state_machine()
       
    def __update_dirty_and_held_transaction_sets(self):
        # remove from the dirty set transactions that have been tottally
        # wiped out
        no_longer_here = set()
        for trans_id in self.dirty_transaction_set.iterkeys():
            self.__transaction_invarient(trans_id)
            if trans_id not in self.__front_end_to_back:
                no_longer_here.add(trans_id)
        for trans_id in no_longer_here:
            del self.dirty_transaction_set[trans_id]
            self.__transaction_invarient(trans_id)

        # remove from the dirty set transactions slated for the held set
        new_for_held_set = set()
        for trans_id in self.dirty_transaction_set.iterkeys():
            self.__transaction_invarient(trans_id)
            state_machine = self.__front_end_to_back[trans_id]
            if state_machine.state == BackendDataStateMachine.BACKEND_HELD:
                new_for_held_set.add(trans_id)
        for trans_id in new_for_held_set:
            del self.dirty_transaction_set[trans_id]
            self.held_transaction_set.add(trans_id)
            self.__transaction_invarient(trans_id)

        # remove from the dirty set if clean
        not_so_dirty = set()
        for trans_id in self.dirty_transaction_set.iterkeys():
            self.__transaction_invarient(trans_id)
            state_machine = self.__front_end_to_back[trans_id]
            if state_machine.state == BackendDataStateMachine.BACKEND_SYNCED:
                not_so_dirty.add(trans_id)
        for trans_id in not_so_dirty:
            del self.dirty_transaction_set[trans_id]
            self.__transaction_invarient(trans_id)

        self._p_changed = True
            
    def __set_state_machine_for_backend_transaction(
        self, trans_id, state_machine):
        assert( trans_id not in self.__front_end_to_back )
        self.__front_end_to_back[trans_id] = state_machine
        self._p_changed = True

    def __create_new_state_machine(self, trans_id, transaction):
        # When following this, it is very important to keep in mind the
        # cycle that flush_backend() takes things through. First it calls
        # run_until_steady_state() for each state, then it calls save()
        # and sets the __last_act flag to LAST_ACT_SAVE if the save worked,
        # finally it calls run_until_steady_state() again for each state.
        # It is possible that the backend may set __last_act to LAST_ACT_RESET
        # during this process through a call to
        # fixeme, above sentance out of date..
        #

        # Fixme, we should document the difference between transiant and
        # persistent (written to database) states, and assert that invariant
        # implication: I think only persistent state would need to check for
        # backend reset

        return BackendDataStateMachine(
            # the initial state machine data
            StateMachineMinChangeDataStore(
                front_end_id=trans_id,
                bo_keep_trans=transaction,
                backend_ids_to_fin_trans={},
                old_backend_ids_to_fin_trans={},
                error_code=BackendDataStateMachine.ERROR_NONE,
                error_string=None,
                ),
            self
            ) # BackendDataStateMachine

    def __raise_if_held_state(self, trans_id):
        if self.__trans_id_in_held_set(trans_id):        
            raise BoKeepBackendException(
                "You can only remove a transaction with a hold on it if "
                "you verify (mark_transaction_for_verification) that it "
                "matches the backend, or explicitly get rid of it ",
                "(mark_transaction_for_forced_remove)" )
    
    def can_write(self):
       # The superclass for all BackendModule s can never write, 
       # because it is a just a base class, you should subclass and
       # return True here when appropriate
       return False

    def remove_backend_transaction(self, backend_ident):
        raise Exception("backend modules must implement "
                        "remove_backend_transaction")

    def verify_backend_transaction(self, backend_ident, fin_trans):
        return True

    def create_backend_transaction(self, fin_trans):
        """Create a transaction inside the actual backend based on fin_trans
        """
        raise Exception("backend modules must implement "
                        "create_backend_transaction")
    def save(self):
        raise Exception("backend modules must implement save()")


class BoKeepBackendException(Exception):
    pass

class BoKeepBackendResetException(Exception):
    """Subclasses of BackendModule can raise this to indicate that
    changes via create_backend_transaction() and remove_backend_changes()
    made since the last successful save have been lost.

    A BackendModule should raise this immediatly when it becomes true, and not
    write new changes (that aren't lost) to the backend prior to raising this.
    """
    pass

