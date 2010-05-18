import os
import glob

from unittest import TestCase, main
from decimal import Decimal
from itertools import chain

from bokeep.backend_modules.module import BackendModule, \
    BackendDataStateMachine, BoKeepBackendException, BoKeepBackendResetException
from bokeep.book import BoKeepBookSet
from bokeep.book_transaction import \
    Transaction, FinancialTransaction, FinancialTransactionLine


class TestTransaction(Transaction):
    fin_trans = FinancialTransaction( (
            FinancialTransactionLine(Decimal(1)),
            FinancialTransactionLine(Decimal(-1)),
            ) )
    
    def get_financial_transactions(self):
       return [self.fin_trans]

CMDS = (REMOVE, CREATE, VERIFY, SAVE, CLOSE) = range(5)

FAILURE_TYPES = \
    (REMOVAL_FAIL, REMOVAL_RESET, CREATION_FAIL, CREATION_RESET,
     SAVE_FAIL, SAVE_RESET, VERIFY_FAIL, VERIFY_RESET) = range(8)

def create_logging_function(func, cmd):
    def logging_function(self, *args, **kargs):
        self.actions_queue.append(tuple( chain(
                    (cmd,), (None,), args) ) )
        return_value = func(self, *args, **kargs)
        self.actions_queue[len(self.actions_queue)-1] = tuple( chain(
                    (cmd,), (return_value,), args) )
        return return_value
    return logging_function

null_function = lambda *args: None

def create_failure_function(func, tag):
    def failure_function(self, *args, **kargs):
        if len(self.programmed_failures[tag]) > 0:
            exception_to_raise, msg, trigger_test = \
                self.programmed_failures[tag].pop()
            if trigger_test(self, *args, **kargs):
                raise exception_to_raise(msg)
        # we want this to execute in two cases,
        # 1) if the first if statement doesn't match, or
        # 2) the second if statement doesn't match
        return func(self, *args, **kargs)
    return failure_function

def create_return_override_function(func, cmd):
    def return_override_function(self, *args, **kargs):
        original_return = func(self, *args, **kargs)
        if len(self.programmed_return[cmd])> 0:
            return self.programmed_return[cmd].pop()
        else:
            return original_return
    return return_override_function

class BackendModuleUnitTest(BackendModule):
    def __init__(self):
        BackendModule.__init__(self)
        self.clear_actions_queue()
        self.clear_programmed_fails()
        self.clear_programmed_return()
        self.counter = 0
        
    def can_write(self):
        return True
    
    remove_backend_transaction = create_logging_function(
        create_failure_function(
            create_failure_function(null_function, REMOVAL_FAIL),
            REMOVAL_RESET),
        REMOVE)
    
    def create_backend_transaction(self, fin_trans):
        self.counter+=1
        return self.counter

    create_backend_transaction = create_logging_function(
        create_failure_function(
            create_failure_function(create_backend_transaction, CREATION_FAIL),
            CREATION_RESET),
        CREATE)

    verify_backend_transaction = create_logging_function(
        create_failure_function(
            create_failure_function(
                create_return_override_function(
                    BackendModule.verify_backend_transaction, VERIFY),
                VERIFY_FAIL),
            VERIFY_RESET),
        VERIFY)


    save = create_logging_function(
        create_failure_function(
            create_failure_function(null_function, SAVE_FAIL),
            SAVE_RESET),
        SAVE)
    close = create_logging_function(BackendModule.close, CLOSE)

    def pop_actions_queue(self):
        return_value = self.actions_queue
        return_value.reverse()
        self.clear_actions_queue()
        return return_value

    def clear_actions_queue(self):
        self.actions_queue = []
    
    def clear_programmed_fails(self):
        self.programmed_failures  = {}
        for tag in FAILURE_TYPES:
            self.programmed_failures[tag] = []

    def program_failure(self, tag, exception_to_raise, msg, trigger_test):
        self.programmed_failures[tag].insert(
            0, (exception_to_raise, msg, trigger_test) )

    def clear_programmed_return(self):
        self.programmed_return = {}
        for cmd in CMDS:
            self.programmed_return[cmd] = []

    def program_return(self, cmd, return_value):
        self.programmed_return[cmd].insert(0, return_value)

class BackendModuleBasicSetup(TestCase):
    """This tests that BackendModule makes calls to the subclass functions
    create_backend_transaction, remove_backend_transaction,
    verify_backend_transaction, save, and close in the expected order, and
    responded in the expected way with calls to mark_transaction_dirty,
    mark_transaction_for_removal, mark_transaction_for_verification,
    mark_transaction_for_hold, mark_transaction_for_forced_remove,
    transaction_is_clean, reason_transaction_is_dirty, flush_backend, and
    backend_reset_occured
    """
    def setUp(self):
        self.backend_module = BackendModuleUnitTest()
        self.transaction = TestTransaction()
        self.fin_trans = self.transaction.get_financial_transactions()[0]

    def pop_all_look_for_save(self):
        actions = self.backend_module.pop_actions_queue()
        self.assertEquals(len(actions), 1)
        self.look_for_save(actions)
        
    def look_for_save(self, actions):
        action1 = actions.pop()
        cmd, return_val = action1
        self.assertEquals(cmd, SAVE)
        self.assertEquals(return_val, None)

    def look_for_verify(self, actions, orig_fin_trans, verify_result=True):
        action1 = actions.pop()
        self.assertEquals(len(action1), 4)
        cmd, return_val, backend_ident, fin_trans = action1
        self.assertEquals(cmd, VERIFY)       
        self.assertEquals(return_val, verify_result)
        self.assertEquals(backend_ident, 1)
        self.assertEquals(fin_trans, orig_fin_trans)

    def look_for_remove(self, actions, backend_ident):
        action = actions.pop()
        self.assertEquals(len(action), 3)
        cmd, return_val, backend_ident = action
        self.assertEquals(cmd, REMOVE)
        self.assertEquals(return_val, None)
        self.assertEquals(backend_ident, backend_ident)

    def look_for_create(self, actions, backend_id, fin_trans):
        action = actions.pop()
        self.assertEquals(len(action), 3)
        cmd, return_val, transaction = action
        self.assertEquals(cmd, CREATE)
        self.assertEquals(return_val, backend_id)
        self.assertEquals(transaction, fin_trans)

    def look_for_empty_actions_queue(self):
        actions = self.backend_module.pop_actions_queue()
        self.assertEquals(len(actions), 0)        

    def assertBackendException(self, callable, *args, **kargs):
        self.assertRaises(
            BoKeepBackendException, callable, *args, **kargs)

    def assertTransactionIsCleanFail(self, trans_id):
        self.assertBackendException(
            self.backend_module.transaction_is_clean,
            trans_id )

    def assertTransactionIsClean(self, trans_id):
        self.assert_(
            self.backend_module.transaction_is_clean(trans_id))
        # this should not throw an exception, idealy we'd check that
        # it always returns None instead of a string, but we're not
        # too worried about forcing that, a backend implementation
        # doesn't need to do that...
        self.assertRaises(
            BoKeepBackendException,
            self.backend_module.reason_transaction_is_dirty,
            trans_id )

    def assertTransactionIsDirty(self, trans_id):
        self.assertFalse(
            self.backend_module.transaction_is_clean(trans_id))

        self.assert_( isinstance(
                self.backend_module.reason_transaction_is_dirty(trans_id),
                str ) )

class BasicBackendModuleTest(BackendModuleBasicSetup):
    def test_null_reset(self):
        # hmm, still saves even if no changes, might want to change that
        # someday
        self.backend_module.flush_backend()
        self.pop_all_look_for_save()

    def test_clean_check_on_none(self):
        self.assertTransactionIsCleanFail(None)

    def test_verify_fail_on_none(self):
        self.assertRaises(
            BoKeepBackendException,
            self.backend_module.mark_transaction_for_verification,
            None )

    def test_remove_fail_on_none(self):
        self.assertRaises(
            BoKeepBackendException,
            self.backend_module.mark_transaction_for_removal,
            None )

    def test_forced_remove_of_non_existent_transaction(self):
        self.assertRaises(
            BoKeepBackendException,
            self.backend_module.mark_transaction_for_forced_remove,
            None )

    def test_hold_on_non_existent_transaction(self):
        self.assertRaises(
            BoKeepBackendException,
            self.backend_module.mark_transaction_for_hold,
            None )

class StartWithInsertSetup(BackendModuleBasicSetup):
    def setUp(self):
        BackendModuleBasicSetup.setUp(self)
        self.front_end_id = 0
        self.backend_module.mark_transaction_dirty(
            self.front_end_id, self.transaction)
        self.FIRST_BACKEND_ID = 1

    def force_remove_known_transaction(self):
        self.backend_module.mark_transaction_for_forced_remove(
            self.front_end_id)

    def verify_known_transaction(self):
        self.backend_module.mark_transaction_for_verification(
            self.front_end_id)        

    # not an actual test case, has to be called by a function
    # that starts with test in the name
    def run_test_of_forced_remove_of_non_held_transaction(self):
        self.assertRaises(
            BoKeepBackendException,
            self.force_remove_known_transaction)

    def run_inspection_of_create_save(self, backend_id=None):
        actions = self.backend_module.pop_actions_queue()
        self.assertEquals(len(actions), 2) # create, save
        self.look_for_create(actions, backend_id, self.fin_trans )
        self.look_for_save(actions)

class StartWithInsertTest(StartWithInsertSetup):
    def test_initial_dirtyness(self):
        self.assertTransactionIsDirty(self.front_end_id)

    def test_forced_remove_of_non_held_transaction(self):
        self.run_test_of_forced_remove_of_non_held_transaction()

    def test_hold_of_uncommited_new_transaction(self):
        self.backend_module.mark_transaction_for_hold(self.front_end_id)
        self.assertTransactionIsDirty(self.front_end_id)
        self.backend_module.flush_backend()
        self.assertTransactionIsDirty(self.front_end_id)
        # this should just save, in the future, we might even avoid the
        # wasted save here
        self.pop_all_look_for_save()

    def test_verify_fail_right_after_insert(self):
        self.assertRaises(
            BoKeepBackendException,
            self.verify_known_transaction )

    def test_re_insert_trouble_when_change(self):
        self.assertRaises(
            BoKeepBackendException,
            self.backend_module.mark_transaction_dirty,
            self.front_end_id, None
            )

    def test_remove_right_after_insert(self):
        self.backend_module.mark_transaction_for_removal(self.front_end_id)
        self.assertTransactionIsDirty(self.front_end_id)
        self.backend_module.flush_backend()
        self.assertTransactionIsCleanFail(self.front_end_id)
        self.pop_all_look_for_save()

    def test_create(self):
        self.backend_module.flush_backend()
        self.assertTransactionIsClean(self.front_end_id)
        self.run_inspection_of_create_save(self.FIRST_BACKEND_ID)

    def test_create_fail(self):
        def check_for_right_financial_trans(backend_mod_self, fin_trans):
            return self.fin_trans == fin_trans
        
        self.backend_module.program_failure(
            CREATION_FAIL, BoKeepBackendException,
            "creation fail", check_for_right_financial_trans)
        self.backend_module.flush_backend()
        self.assertTransactionIsDirty(self.front_end_id)
        self.run_inspection_of_create_save(None)
        # creation process should work now that programmed fail is gone
        self.test_create()
               
    def test_create_lost_by_reset(self):
        def check_for_right_financial_trans(backend_mod_self, fin_trans):
            return self.fin_trans == fin_trans
        
        self.backend_module.program_failure(
            CREATION_RESET, BoKeepBackendResetException,
            "creation lost to reset", check_for_right_financial_trans)
        self.backend_module.flush_backend()
        self.assertTransactionIsDirty(self.front_end_id)        
        actions = self.backend_module.pop_actions_queue()
        self.assertEquals(len(actions), 1) # create
        self.look_for_create(actions, None, self.fin_trans )
        # creation process should work now that programmed reset is gone
        self.test_create()

    def test_create_fail_followed_by_save_throwing_reset(self):
        def check_for_right_financial_trans(backend_mod_self, fin_trans):
            return self.fin_trans == fin_trans
        
        self.backend_module.program_failure(
            CREATION_FAIL, BoKeepBackendException,
            "creation fail", check_for_right_financial_trans)

        reason_for_reset = "reset called on save()"
        self.backend_module.program_failure(
            SAVE_RESET, BoKeepBackendResetException,
            reason_for_reset, lambda backend_mod_self: True )

        self.backend_module.flush_backend()
        self.assertTransactionIsDirty(self.front_end_id)
        self.run_inspection_of_create_save(backend_id=None)
        full_error_string = \
            self.backend_module.reason_transaction_is_dirty(self.front_end_id)
        self.assert_(full_error_string.endswith(reason_for_reset) )
        self.assert_(full_error_string.startswith(
            "error code: %s"  % BackendDataStateMachine.ERROR_OTHER) )
        # creation process should work now that programmed reset is gone
        self.test_create()

class StartWithInsertAndFlushSetup(StartWithInsertSetup):
    def setUp(self):
        StartWithInsertSetup.setUp(self)
        self.backend_module.flush_backend()
        self.backend_module.pop_actions_queue()
        self.SECOND_BACKEND_ID = self.FIRST_BACKEND_ID+1

    def run_test_of_transaction_verify(self, verify_result=True):
        # this should do a VERIFY and a SAVE
        self.verify_known_transaction()
        self.assertTransactionIsDirty(self.front_end_id)
        self.backend_module.flush_backend()
        self.assertTransactionIsClean(self.front_end_id)
        self.look_for_actions_from_verify(verify_result)

    def look_for_actions_from_verify(self, verify_result=True):
        actions = self.backend_module.pop_actions_queue()
        self.assertEquals(len(actions), 2) # verify, save
        self.look_for_verify(actions, self.fin_trans, verify_result)
        self.look_for_save(actions)        

    def remove_known_transaction_and_flush(self):
        self.backend_module.mark_transaction_for_removal(self.front_end_id)
        self.assertTransactionIsDirty(self.front_end_id)
        self.backend_module.flush_backend()

    def run_test_of_transaction_remove(self):
        self.remove_known_transaction_and_flush()

        self.look_for_normal_remove_sequence()

    def look_for_normal_remove_sequence(self):
        actions = self.backend_module.pop_actions_queue()
        self.assertEquals(len(actions), 3) # verify, remove, save
        self.look_for_verify(actions, self.fin_trans)
        self.look_for_remove(actions, self.FIRST_BACKEND_ID)
        self.look_for_save(actions)

    def run_test_fail_if_dirty_mark_in_hold(self):
        self.assertRaises(
            BoKeepBackendException,
            self.backend_module.mark_transaction_dirty,
            self.front_end_id, self.transaction )

    def run_test_fail_if_removal_in_hold(self):
        self.assertRaises(
            BoKeepBackendException,
            self.backend_module.mark_transaction_for_removal,
            self.front_end_id )

class StartWithInsertAndFlushTests(StartWithInsertAndFlushSetup):
    def test_dirty_after_flush(self):
        self.assertTransactionIsClean(self.front_end_id)

    def test_forced_remove_of_non_held_transaction(self):
        self.run_test_of_forced_remove_of_non_held_transaction()
        
    def test_transaction_verify(self):
        self.run_test_of_transaction_verify()
    
    def test_multi_verify(self):
        for i in xrange(20):
            self.verify_known_transaction()
        self.test_transaction_verify()

    def test_verify_fail(self):
        reason_for_backend_verify_fail = "this is just a test, not a real " \
            "failure on verify"
        def test_for_correct_backend_id(backend_mod_self, backend_id,
                                        fin_trans):
            return backend_id == self.FIRST_BACKEND_ID and \
                fin_trans == self.fin_trans
        self.backend_module.program_failure(
            VERIFY_FAIL, BoKeepBackendException,
            reason_for_backend_verify_fail, test_for_correct_backend_id)

        # this should do a VERIFY and a SAVE
        self.verify_known_transaction()
        self.assertTransactionIsDirty(self.front_end_id)
        self.backend_module.flush_backend()
        self.assertTransactionIsDirty(self.front_end_id)
        self.look_for_actions_from_verify(None)
        self.run_test_of_transaction_verify()

    def test_transaction_hold(self):
        # this should just SAVE
        self.backend_module.mark_transaction_for_hold(self.front_end_id)
        self.backend_module.flush_backend()
        self.pop_all_look_for_save()

    def test_multi_hold(self):
        # this should just SAVE
        for i in xrange(20):
            self.backend_module.mark_transaction_for_hold(self.front_end_id)
        self.test_transaction_hold()

    def test_transaction_dirty_refresh(self):
        self.backend_module.mark_transaction_dirty(
            self.front_end_id, self.transaction)
        self.assertTransactionIsDirty(self.front_end_id)
        self.backend_module.flush_backend()
        self.assertTransactionIsClean(self.front_end_id)

        actions = self.backend_module.pop_actions_queue()
        self.assertEquals(len(actions), 4) # verify, remove, create, save

        self.look_for_verify(actions, self.fin_trans)
        self.look_for_remove(actions, self.FIRST_BACKEND_ID)
        self.look_for_create(actions, self.SECOND_BACKEND_ID, self.fin_trans)
        self.look_for_save(actions)

    def test_transaction_remove(self):
        self.run_test_of_transaction_remove()
        self.assertTransactionIsCleanFail(self.front_end_id)
       
    def test_failed_remove(self):
        reason_for_backend_fail = "this is just a test, not a real failure " \
            "on remove"
        def test_for_correct_backend_id(backend_mod_self, backend_id):
            return backend_id == self.FIRST_BACKEND_ID
        self.backend_module.program_failure(
            REMOVAL_FAIL, BoKeepBackendException,
            reason_for_backend_fail, test_for_correct_backend_id)

        self.run_test_of_transaction_remove()
        self.assertTransactionIsDirty(self.front_end_id)
        full_error_string = \
            self.backend_module.reason_transaction_is_dirty(self.front_end_id)
        self.assert_(full_error_string.endswith(reason_for_backend_fail) )
        self.assert_(full_error_string.startswith(
            "error code: %s"  % BackendDataStateMachine.ERROR_CAN_NOT_REMOVE) )

        # check that it works next time around
        self.test_transaction_remove()

    def test_reset_lost_remove(self):
        reason_for_backend_reset = "this is just a test, not a real reset " \
            "on remove"
        def test_for_correct_backend_id(backend_mod_self, backend_id):
            return backend_id == self.FIRST_BACKEND_ID
        self.backend_module.program_failure(
            REMOVAL_RESET, BoKeepBackendResetException,
            reason_for_backend_reset, test_for_correct_backend_id)

        self.backend_module.mark_transaction_for_removal(self.front_end_id)
        self.assertTransactionIsDirty(self.front_end_id)
        self.backend_module.flush_backend()

        actions = self.backend_module.pop_actions_queue()
        self.assertEquals(len(actions), 2) # verify, remove
        self.look_for_verify(actions, self.fin_trans)
        self.look_for_remove(actions, self.FIRST_BACKEND_ID)

        self.assertTransactionIsDirty(self.front_end_id)

    def test_after_verify_inconsist_triggered_by_verify(self):
        self.backend_module.program_return(VERIFY, False)
        self.verify_known_transaction()
        self.assertTransactionIsDirty(self.front_end_id)
        self.backend_module.flush_backend()
        self.assertTransactionIsDirty(self.front_end_id)
        self.look_for_actions_from_verify(False)
        reason_dirty = \
            self.backend_module.reason_transaction_is_dirty(self.front_end_id)
        self.assert_(reason_dirty.startswith(
                "error code: %s" % BackendDataStateMachine.ERROR_VERIFY_FAILED
                ))
        self.backend_module.flush_backend()
        self.assertTransactionIsDirty(self.front_end_id)
        reason_dirty = \
            self.backend_module.reason_transaction_is_dirty(self.front_end_id)
        self.assert_(reason_dirty.startswith(
                "error code: %s" % BackendDataStateMachine.ERROR_VERIFY_FAILED
                ))
        self.pop_all_look_for_save()

        # can't mark dirty, can't remove normally
        self.run_test_fail_if_dirty_mark_in_hold()
        self.run_test_fail_if_removal_in_hold()

        # let it fail the next verification, again
        self.backend_module.program_return(VERIFY, False)
        self.verify_known_transaction()
        self.assertTransactionIsDirty(self.front_end_id)
        self.backend_module.flush_backend()
        self.assertTransactionIsDirty(self.front_end_id)
        self.run_test_fail_if_dirty_mark_in_hold()
        self.look_for_actions_from_verify(False)
        self.run_test_of_transaction_verify()

    def test_after_verify_fail_triggered_by_verify(self):
        reason_for_backend_fail = "this is just a test, not a real failure " \
            "on verify"
        def test_for_correct_backend_id(
            backend_mod_self, backend_id, fin_trans):
            return backend_id == self.FIRST_BACKEND_ID and \
                fin_trans == self.fin_trans
        self.backend_module.program_failure(
            VERIFY_FAIL, BoKeepBackendException,
            reason_for_backend_fail, test_for_correct_backend_id)
        self.verify_known_transaction()
        self.assertTransactionIsDirty(self.front_end_id)
        self.backend_module.flush_backend()
        self.assertTransactionIsDirty(self.front_end_id)
        self.look_for_actions_from_verify(None)
        self.run_test_of_transaction_verify()

    def test_after_verify_inconsist_triggered_by_removal(self):
        self.backend_module.program_return(VERIFY, False)
        self.remove_known_transaction_and_flush()
        actions = self.backend_module.pop_actions_queue()
        self.assertEquals(len(actions), 2) # verify, save
        self.look_for_verify(actions, self.fin_trans, False)
        self.look_for_save(actions)
        self.assertTransactionIsDirty(self.front_end_id)
        self.backend_module.flush_backend()
        self.pop_all_look_for_save()
        # can't mark dirty, can't remove normally
        self.run_test_fail_if_dirty_mark_in_hold()
        self.run_test_fail_if_removal_in_hold()

    def test_after_verify_fail_triggered_by_removal(self):
        reason_for_backend_fail = "this is just a test, not a real failure " \
            "on verify"
        def test_for_correct_backend_id(
            backend_mod_self, backend_id, fin_trans):
            return backend_id == self.FIRST_BACKEND_ID and \
                fin_trans == self.fin_trans
        self.backend_module.program_failure(
            VERIFY_FAIL, BoKeepBackendException,
            reason_for_backend_fail, test_for_correct_backend_id)
        self.remove_known_transaction_and_flush()
        actions = self.backend_module.pop_actions_queue()
        self.assertEquals(len(actions), 2) # verify, save
        self.look_for_verify(actions, self.fin_trans, None)
        self.look_for_save(actions)
        self.assertTransactionIsDirty(self.front_end_id)
        self.backend_module.flush_backend()
        self.look_for_normal_remove_sequence()

class StartWithInsertFlushAndHoldSetup(StartWithInsertAndFlushSetup):
    def setUp(self):
        StartWithInsertAndFlushSetup.setUp(self)
        self.backend_module.mark_transaction_for_hold(self.front_end_id)
        self.backend_module.flush_backend()
        self.backend_module.pop_actions_queue()


class InsertFlushAndHoldTest(StartWithInsertFlushAndHoldSetup):
    def test_after_flush(self):
        self.assertTransactionIsDirty(self.front_end_id)

    def test_success_force_remove(self):
        self.look_for_empty_actions_queue()        
        self.force_remove_known_transaction()
        self.assertTransactionIsDirty(self.front_end_id)
        self.backend_module.flush_backend()
        self.assertTransactionIsCleanFail(self.front_end_id)

        actions = self.backend_module.pop_actions_queue()
        # expecting REMOVE and SAVE
        self.assertEquals(len(actions), 2)
        self.look_for_remove(actions, self.FIRST_BACKEND_ID)
        self.look_for_save(actions)

    def test_success_verify_in_hold(self):
        self.look_for_empty_actions_queue()
        self.run_test_of_transaction_verify()

    def test_fail_if_dirty_mark_in_hold(self):
        self.run_test_fail_if_dirty_mark_in_hold()

    def test_fail_if_removal_in_hold(self):
        self.run_test_fail_if_removal_in_hold()

if __name__ == "__main__":
    main()
        

