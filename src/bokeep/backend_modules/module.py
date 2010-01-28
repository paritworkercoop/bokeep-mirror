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

BACKEND_VERIFICATION_REQUESTED = False

class BackendModule(Persistent):
    """Illustrates the Bo-Keep backend module API

    A Bo-Keep backend module does not need to be a subclass of
    bokeep.backend_modules.module.BackendModule, but it must implement the
    following functions provided here:
    mark_transaction_dirty, mark_transaction_for_removal,
    mark_transaction_for_verification, transaction_is_clean,
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

    LAST_ACT_NONE, LAST_ACT_SAVE, LAST_ACT_RESET = range(3)

    def __init__(self):
        Persistent.__init__(self)
        self.__front_end_to_back = {}
        self.dirty_transaction_set = {}
        self.__last_act = self.LAST_ACT_NONE

    # START MANDATORY BO-KEEP BACKEND MODULE API
        
    @ends_with_commit
    def mark_transaction_dirty(self, trans_id, transaction):
        """Indicate a bo-keep transaction is not up to date in the backend.

        This doesn't trigger the backend update itself to occure, that only
        happens when flush_backend is called

        trans_id -- Bo-keep identifier for the transaction
        transaction -- The actual bo-keep transaction
        """
        self.dirty_transaction_set[trans_id] = transaction
        if not self.__has_backend_id_state_machine(trans_id):
            self.__set_state_macine_for_backend_transaction(
                trans_id,
                self.__create_new_state_machine(trans_id, transaction)
                )
        self._p_changed = True

    @ends_with_commit
    def mark_transaction_for_removal(self, trans_id):
        """Indicate a bo-keep transaction should be removed from the backend

        This doesn't trigger the backend to immediately do the removal, that
        only happens when flush_backend is called

        trans_id -- Bo-Keep transaction i
        """
        self.dirty_transaction_set[trans_id] = None
        self._p_changed = True
#        backend_idents = \
#            self.get_backend_transaction_identifier(frontend_ident)
#        if frontend_ident in self.front_end_to_back_id:
#            del self.front_end_to_back_id[frontend_ident]
#        if frontend_ident in self.dirty_transaction_set:
#            del self.dirty_transaction_set[frontend_ident]
#        self._p_changed = True
#        if backend_idents != None:
#            for backend_ident in backend_idents:
#                self.remove_backend_transaction(backend_ident)

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
        if trans_id in self.dirty_transaction_set and \
                self.dirty_transaction_set[trans_id] != \
                BACKEND_VERIFICATION_REQUESTED:
            raise BoKeepBackendException(
                "You can't request verification on a transaction with changes "
                "or being deleted, call mark_transaction_for_verification() "
                "again after flush_backend deals with those changes" )
        self.dirty_transaction_set[trans_id] = BACKEND_VERIFICATION_REQUESTED
        self._p_changed = True

    def transaction_is_clean(self, trans_id):
        """Returns True if a transaction is not dirty, marked for removal,
        or in any other state than the normal one
        """
        return trans_id not in self.dirty_transaction_set

    def reason_transaction_is_dirty(self, trans_id):
        """Returns a string that describes why a particular transaction is still
        dirty, marked for removal, or in any other non-clean / non-normal state.

        You should only call this if you've first called transaction_is_clean(),
        otherwise it isn't meaningful and may return non-String values like
        None

        You will get an error if you call this when trans_id doesn't
        exist
        """
        return self.dirty_transaction_set[trans_id].data.get_value(
            'error_string')
    
    def flush_backend(self):
        """Take all transactions that are dirty or marked for removal
        writes them out / removes them out if possible.

        When this is done, it does a zopedb transaction commit, if you're
        sharing a zopedb thread with this you'll want to be sure your data
        is in a state you're comfortable having commited
        """
        # if we can write to the backend
        if self.can_write():
            # for each dirty transaction do all the things that are needed
            # prior to a save()
            self.__advance_all_dirty_transaction_state_machine()
            self._p_changed = True
            transaction.get().commit()
            # save, and let all dirty transactions change thier state
            # the the knowledge that a save just took place
            try:
                self.save()
                self.__reason_for_save_fail = None
                assert(self.__last_act == self.LAST_ACT_NONE)
                self.__last_act = self.LAST_ACT_SAVE
                self.__advance_all_dirty_transaction_state_machine()
                self.__remove_dirty_transaction_state_machines_that_lost_dirty()
                self.__last_act = self.LAST_ACT_NONE
            except BoKeepBackendException, e:
                self.__reason_for_save_fail = e.message
            transaction.get().commit()
            self._p_changed = True

    def close(self):
        """Instructs the module to release any resources being used to
        access the backend.

        This should be called when done with a backend module.
        """
        pass

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
    def verify_trans_and_close(self, trans_id)
        """When this is done, it does a zopedb transaction commit, if you're
        sharing a zopedb thread with this you'll want to be sure your data
        is in a state you're comfortable having commited
        """
        self.mark_transaction_for_verification(trans_id)
        self.flush_backend()
        is_clean = self.transaction_is_clean(trans_id)
        self.close()
        return is_clean

    @ends_with_commit
    def setattr(self, attr, value):
        """When this is done, it does a zopedb transaction commit, if you're
        sharing a zopedb thread with this you'll want to be sure your data
        is in a state you're comfortable having commited
        """
        setattr(self, attr, value)
        self.flush_backend()

    # END MANDATORY BO-KEEP BACKEND MODULE API

    def __advance_all_dirty_transaction_state_machine(self):
        for key, value in self.dirty_transaction_set.iteritems():
            self.get_backend_state_machine(key).run_until_steady_state()

    def __remove_dirty_transaction_state_machines_that_lost_dirty(self):
        not_so_dirty = set()
        for key in self.dirty_transaction_set.iterkeys():
            state_machine = self.get_backend_state_machine(key)
            if not state_machine.data.get_value('dirty_flag'):
                not_so_dirty.add(key)
        for trans_id in not_so_dirty:
            del self.dirty_transaction_set[trans_id]
            
    def __set_state_machine_for_backend_transaction(
        self, trans_id, backend_identifier):
        assert( not __has_state_machine_for_frontend_id(trans_id) )
        self.__front_end_to_back_id[trans_id] = backend_identifier
        self._p_changed = True

    def __get_backend_transaction_state_machine(self, trans_id):
        if self.__has_state_machine_for_frontend_id(trans_id):
            return self.__front_end_to_back_id[trans_id]
        else:
            return None

    def __has_state_machine_for_frontend_id(self, trans_id):
        return trans_id in in self.__front_end_to_back_id

    def __remove_backend_transactions_state_machine(self,
                                                    state_machine, next_state):
        """Removes any backend transactions listed in the state machine data

        Any backend transactions not removed remain in the list, and the error
        flag is set if this happens
        """
        # this function doesn't make sense to call when the error flag is up
        assert(not state_machine.data.get_value('error_flag'))
        backend_ids = state_machine.data.get_value('backend_ids')

        removed_backend_ids = set()
        old_backend_ids = set(backend_ids)
        try:
            for backend_id in backend_ids:
                remove_backend_transaction(backend_id)
                removed_backend_ids.add(backend_id)
        except BoKeepBackendException, e:
            error_flag = True
            error_string = e.message
        backend_ids = backend_ids.difference(removed_backend_ids)

        return state_machine.data.duplicate_and_change(
            backend_ids=backend_ids
            old_backend_ids=old_backend_ids,
            error_flag=error_flag,
            error_string=error_string )

    def __remove_transaction_state_machine(self,
                                           state_machine, next_state):
        """Removes any backend transactions listed in the state machine
        data, and if they were all removed without error, the reference
        to the state machine is removed from __front_end_to_back_id
        """
        # this function doesn't make sense to call when the error flag is up
        assert(not state_machine.data.get_value('error_flag'))

        # we shouldn't remove the state machine until there are no backend
        # transactions
        assert(len(state_machine.data.get_value('backend_ids')) == 0)

        del self.__front_end_to_back_id[
            state_machine.data.get_value('front_end_id')]
        return state_machine.data # no changes

    def __remove_requested_state_machine(self, state_machine, next_state):
        return self.dirty_transaction_set[
            state_machine.data.get_value('front_end_id')] == None

    def __last_act_save_state_machine(self, state_machine, next_state):
        return self.__last_act == self.LAST_ACT_SAVE

    def __last_act_reset_state_machine(self, state_macine, next_state):
        return self.__last_act == self.LAST_ACT_RESET

    def __create_backend_transaction_state_machine(self,
                                                   state_machine, next_state):
        # this doesn't make any sense if there are backend ids in existence
        assert( len(state_machine.data.get_value('backend_ids')) == 0 )
        # nor should there be errors
        assert( not state_machine.data.get_value('error_flag') )
        
        backend_ids = state_machine.data.get_value('backend_ids')
        old_backend_ids = set(backend_ids)
        last_fin_trans_list = state_machine.data.get_value(fin_trans_list)
        try:
            fin_trans_list = list(bo_keep_trans.get_financial_transactions())
            for fin_trans in fin_trans_list:
                backend_ids.add(create_backend_transaction(fin_trans) )
        # can be raised by bo_keep_trans.get_financial_transactions() and
        # create_backend_transaction()
        except BoKeepTransactionNotMappableToFinancialTransaction, e:
            error_flag = True
            error_string = e.message

        return state_machine.data.duplicate_and_change(
            backend_ids=backend_ids,
            old_backend_ids=old_backend_ids,
            last_fin_trans_list=last_fin_trans_list,
            fin_trans_list=fin_trans_list,
            error_flag=error_string,
            error_string=error_string,
            )

    def __clear_error_flag_and_msg_state_machine(self,
                                                 state_machine, next_state):
        return state_machine_.data.duplicate_and_change(
            error_flag=False,
            error_string=None)

    def __backend_data_verify_state_machine(self, state_machine, next_state):
        # try to verify each backend transaction (if it exists)
        # set error flag if something is found in the backend we didn't expect
        return state_machine

    def self.__backend_data_remove_old_transactions(self,
                                                    state_machine, next_state):
        # try to remove old backend transactions...
        return state_machine
    
    def __record_reason_for_reset_state_machine(self,
                                                state_machine, next_state):
        # set the error flag and msg, poll the underlying module
        #
        # should self.__reason_for_save_fail play a role?
        pass

    def __in_dirty_set_state_machine(self, state_machine, next_state):
        return not self.transaction_is_clean(
            state_machine.data.get_value('front_end_id') )

    def __set_dirty_flag_state_machine(self, state_machine, next_state):
        return state_machine_.data.duplicate_and_change(
            dirty_flag=True)

    def __clear_dirty_flag_state_machine(self, state_machine, next_state):
        return state_machine_.data.duplicate_and_change(
            dirty_flag=False)

    def __create_new_state_machine(self, trans_id, transaction):
        # These are the states a transaction can be in the backend
        #
        # When following this, it is very important to keep in mind the
        # cycle that flush_backend() takes things through. First it calls
        # run_until_steady_state() for each state, then it calls save()
        # and sets the __last_act flag to LAST_ACT_SAVE if the save worked,
        # finally it calls run_until_steady_state() again for each state.
        # It is possible that the backend may set __last_act to LAST_ACT_RESET
        # during this process through a call to 
        #
         # backend transactions do not yet exist
        (NO_BACKEND_EXIST, 
         # an attempt was made to create backend transaction
         BACKEND_CREATION_TRIED,
         # an attempt was made to create a backend transaction, but it never
         # made it, and we don't want to muck with it again until there is a
         # save
         BACKEND_ERROR_WAIT_SAVE,
         # an attempt was made to create a backend transaction, but it never
         # made it
         BACKEND_ERROR,
         # The backend is in sync with the front end, stay in this state
         # until a transaction is marked as dirty
         BACKEND_SYCNED,
         # The backend is out of sync, and will soon be updated
         BACKEND_OUT_OF_SYNC,
         # despite past errors, a new attempt is ready to be be made made to
         # synchronize
         BACKEND_ERROR_TRY_AGAIN,
         # we just forgot past errors, ready for regeneration steps
         BACKEND_ERROR_FORGOTON_TRY_AGAIN,
         # preparing to remove old backend transactions, verification
         # just took place on the way here
         BACKEND_OLD_TO_BE_REMOVED,
         # an attempt was just made to remove backend transactions, will
         # move on to re-creating them if that worked
         BACKEND_OLD_JUST_TRIED_REMOVE,

         # still missing, states that allow a verification request
         #
         # missing logic to allow a transaction with a mismatch in the
         # backend to just screw over the backend anyway (if specifically
         # requested), and a transaction to be markable for no longer
         # syncing and to just leave the backend be without trying to check
         # anymore...
         ) = range(?)

        return FunctionAndDataDrivenStateMachine(
            (
                # Rules for state NO_BACKEND_EXIST
                #
                  # If a transaction is marked for removal but is in this state
                  # all we have to do is remove the state machine
                  # next state won't matter
                ( (self.__remove_requested_state_machine,
                   self.__remove_transaction_state_machine, NO_BACKEND_EXIST ),
                  # Otherwise, always move to NO_BACKEND_TRIED and try to
                  # create the backend transaction
                  (state_machine_always_true,
                   self.__create_backend_transaction_state_machine,
                   BACKEND_CREATION_TRIED),
                  ), # end rules for state NO_BACKEND_EXIST

                # Rules for state BACKEND_CREATION_TRIED
                #
                  # If there was an error when attempting to create the
                  # backend transaction, go to the error state
                ( (self.__error_in_state_machine_data,
                   state_machine_do_nothing, BACKEND_ERROR_WAIT_SAVE),
                  # If the transaction was created in the backend, but
                  # lost because a save couldn't take place, we'll just
                  # have to try again
                  (self.__last_act_reset_state_machine,
                   state_machine_do_nothing,
                   BACKEND_ERROR_TRY_AGAIN),
                  # Otherwise we're just waiting for the save to work out
                  (self.__last_act_save_state_machine,
                   self.__clear_dirty_flag_state_machine, BACKEND_SYNCED)
                    ), # end rules for state BACKEND_CREATION_TRIED

                # Rules for state BACKEND_ERROR_WAIT_SAVE
                  # no big deal if save never happned and we lost it...,
                  # just try again
                ( (self.__last_act_reset_state_machine,
                   clear_error_flag_and_msg_state_machine,
                   BACKEND_ERROR_TRY_AGAIN),
                  # otherwise we wait until there is a save
                  (self.__last_act_save_state_machine,
                   state_machine_do_nothing, BACKEND_ERROR),
                  ), # end rules for state BACKEND_ERROR_WAIT_SAVE

                # rules for BACKEND_ERROR
                  # As long as the last thing that happened was a save,
                  # we stay here
                ( (self.__last_act_save_state_machine,
                   state_machine_do_nothing, BACKEND_ERROR),

                  # Now we can move on and try again to commit..
                  (state_machine_always_true,
                   self.__clear_error_flag_and_msg_state_machine,
                   BACKEND_ERROR_TRY_AGAIN),
                  ), # end rules for state BACKEND_ERROR
                   
                # Rules for state BACKEND_SYNCHED
                  # check if dirty in dirty_transaction_set, if so,
                  # set the dirty flag in the state machine
                ( (self.__in_dirty_set_state_machine,
                   self.__set_dirty_flag_state_machine, BACKEND_OUT_OF_SYNC),
                  ), # end rules for state BACKEND_SYNCHED

                # Rules for state BACKEND_OUT_OF_SYNC
                  # always check if backend data has changed
                ( (self.__last_act_reset_state_machine,
                   do_nothing_state_machine,
                   BACKEND_OUT_OF_SYNC),
                  (state_machine_always_true,
                   self.__backend_data_verify_state_machine,
                   BACKEND_OLD_TO_BE_REMOVED)
                    ), # end rules for state BACKEND_OUT_OF_SYNC

                # Rules for state BACKEND_ERROR_TRY_AGAIN
                #
                  # If we got here because of a reset, just wait in this
                  # state and record the reason
                ( (self.__last_act_reset_state_machine,
                   self.__record_reason_for_reset_state_machine,
                   BACKEND_ERROR_TRY_AGAIN),
                  # otherwise we are ready to try again, the first step
                  # being data verification prior to removing anything
                  # sitting around in the backend
                  (state_machine_always_true,
                   self.__clear_error_flag_and_msg_state_machine,
                   BACKEND_ERROR_FORGOTON_TRY_AGAIN),
                  ), # end rules for state BACKEND_ERROR_TRY_AGAIN
                
                # Rules for state BACKEND_ERROR_FORGOTON_TRY_AGAIN
                ( (state_machine_always_true,
                   self.__backend_data_verify_state_machine,
                   BACKEND_OLD_TO_BE_REMOVED),
                  ) # end rules for state BACKEND_ERROR_FORGOTON_TRY_AGAIN

                # Rules for state BACKEND_OLD_TO_BE_REMOVED
                ( (self.__error_in_state_machine_data,
                   state_machine_do_nothing, BACKEND_ERROR_WAIT_SAVE),
                  # is this really fair if we got here from
                  # BACKEND_SYNCHED->BACKEND_OUT_OF_SYNC, if there was
                  # never an error and just a reset, what's the big deal?
                  # why go into an error try again state and not just
                  # back to BACEND_OUT_OF_SYNC?, perhaps there should be a
                  # separate path...
                  (self.__last_act_reset_state_machine,
                   do_nothing_state_machine, BACKEND_ERROR_TRY_AGAIN),
                  (state_machine_always_true,
                   self.__backend_data_remove_old_transactions,
                   BACKEND_OLD_JUST_TRIED_REMOVE),
                  ), # end rules for state BACKEND_OLD_TO_BE_REMOVED

                # Rules for BACKEND_OLD_JUST_TRIED_REMOVE
                ( (self.__error_in_state_machine_data,
                   state_machine_do_nothing, BACKEND_ERROR_WAIT_SAVE),
                  # see comment on similar rule in BACKEND_OLD_TO_BE_REMOVED..
                  (self.__last_act_reset_state_machine,
                   do_nothing_state_machine, BACKEND_ERROR_TRY_AGAIN),
                  # if we got so far as to verify no problem with
                  # backend data, and no problem with removal, 
                  (state_machine_always_true,
                   state_machine_do_nothing, NO_BACKEND_EXIST
                   ),
                  ), # end rules for state BACKEND_OLD_JUST_TRIED_REMOVE

                ) # end state list
            NO_BACKEND_EXIST, # initial_state
            # the initial state machine data
            StateMachineMinChangeDataStore(
                front_end_id=trans_id,
                bo_keep_trans=transaction,
                backend_ids=set(),
                old_backend_ids=set(),
                error_flag=False,
                error_string=None,
                fin_trans_list=(),
                last_fin_trans_list=(),
                dirty_flag=True,
                )
            )
        

    def can_write(self):
       # The superclass for all BackendModule s can never write, 
       # because it is a just a base class, you should subclass and
       # return True here when appropriate
       return False

    def remove_backend_transaction(self, backend_ident):
        raise Exception("backend modules must implement "
                        "remove_backend_transaction")

    def verify_backend_transaction(self, backend_ident):
        raise True

    def create_backend_transaction(self, fin_trans):
        """Create a transaction inside the actual backend based on fin_trans
        """
        raise Exception("backend modules must implement "
                        "create_backend_transaction")

    def backend_reset_occured(self):
        """Invoked by a subclass of BackendModule to indicate that
           changes via create_backend_transaction() and remove_backend_changes()
           made since the last successful save were lost.
        """
        assert(self.__last_act == self.LAST_ACT_NONE)
        self.__last_act = self.LAST_ACT_RESET
        self.__advance_all_dirty_transaction_state_machine()
        self.__last_act = self.LAST_ACT_NONE

    def save(self):
        raise Exception("backend modules must implement save()")

    def flush_transaction(self, entity_identifier):
        backend_idents = \
            self.get_backend_transaction_identifier(entity_identifier)
        if None != backend_idents:
            for backend_ident in backend_idents:
                self.remove_backend_transaction(backend_ident)

        # get financial transactions from the specified bokeep transaction
        # put each of these in the backend, and store a mapping of the
        # bokeep transaction identifier and the associated backend transactions
        transaction = self.dirty_transaction_set[entity_identifier]
        self.set_backend_transaction_identifier(
            entity_identifier,
            tuple( 
                self.create_backend_transaction(fin_trans)
                for fin_trans in transaction.get_financial_transactions() )
            )
        self._p_changed = True

class BoKeepBackendException(Exception):
    def __init__(self, msg=""):
        Exception.__init__(msg)
