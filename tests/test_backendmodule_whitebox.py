from unittest import TestCase, main
from decimal import Decimal
from itertools import chain

from bokeep.backend_modules.module import BackendModule, \
    BackendDataStateMachine, BoKeepBackendException, BoKeepBackendResetException
from bokeep.book import BoKeepBookSet
from bokeep.book_transaction import \
    Transaction, FinancialTransaction, FinancialTransactionLine

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

    
class TestTransaction(Transaction):
    fin_trans = FinancialTransaction( (
            FinancialTransactionLine(Decimal(1)),
            FinancialTransactionLine(Decimal(-1)),
            ) )
    
    def get_financial_transactions(self):
       return [self.fin_trans]

class BackendModuleWhiteboxStartWithInsertSetup(TestCase):
    def setUp(self):
        self.backend_module = BackendModuleUnitTest()
        self.transaction = TestTransaction()
        self.fin_trans = self.transaction.get_financial_transactions()[0]
        self.front_end_id = 0
        self.backend_module.mark_transaction_dirty(
            self.front_end_id, self.transaction)    
        self.FIRST_BACKEND_ID = 1

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

    def run_inspection_of_create_save(self, backend_id=None):
        actions = self.backend_module.pop_actions_queue()
        self.assertEquals(len(actions), 2) # create, save
        self.look_for_create(actions, backend_id, self.fin_trans )
        self.look_for_save(actions)

class BackendModuleWhiteboxInsertTests(
    BackendModuleWhiteboxStartWithInsertSetup):

    def test_create_lost_by_reset(self):
        def check_for_right_financial_trans(backend_mod_self, fin_trans):
            return self.fin_trans == fin_trans
        
        self.backend_module.program_failure(
            CREATION_RESET, BoKeepBackendResetException,
            "creation lost to reset", check_for_right_financial_trans)
        self.backend_module.flush_backend()
        actions = self.backend_module.pop_actions_queue()
        self.assertEquals(len(actions), 1) # create
        state_machine = self.backend_module._BackendModule__front_end_to_back[
            self.front_end_id]
        self.assertEquals(state_machine.state,
                          BackendDataStateMachine.BACKEND_OUT_OF_SYNC)
        
        # creation process should work now that programmed reset is gone
        #self.backend_module.flush_backend()
        self.backend_module.\
            _BackendModule__advance_all_dirty_transaction_state_machine(True)
        self.assertEquals(state_machine.state,
                          BackendDataStateMachine.BACKEND_CREATION_TRIED)
        dirty_set_copy = self.backend_module.dirty_transaction_set.copy()
        self.backend_module.save()
        for dirty_trans_id in \
                self.backend_module.dirty_transaction_set.iterkeys():
            self.backend_module.dirty_transaction_set[dirty_trans_id] = \
                BackendDataStateMachine.LAST_ACT_SAVE
            self._p_changed = True
        self.backend_module.\
            _BackendModule__advance_all_dirty_transaction_state_machine()
        self.backend_module.\
            _BackendModule__update_dirty_and_held_transaction_sets()
        for trans_id, original_input_value in \
                dirty_set_copy.iteritems():
            if trans_id in self.backend_module.dirty_transaction_set:
                self.backend_module.dirty_transaction_set[trans_id] = \
                    original_input_value
        self.assertEquals(state_machine.state,
                          BackendDataStateMachine.BACKEND_SYNCED)
        
        self.assertTransactionIsClean(self.front_end_id)
        self.run_inspection_of_create_save(self.FIRST_BACKEND_ID)


class BackendModuleWhiteboxStartWithInsertAndFlushSetup(
    BackendModuleWhiteboxStartWithInsertSetup):

    def setUp(self):
        BackendModuleWhiteboxStartWithInsertSetup.setUp(self)
        self.backend_module.flush_backend()
        self.backend_module.pop_actions_queue()
        self.SECOND_BACKEND_ID = self.FIRST_BACKEND_ID+1    
    
class BackendModuleWhiteboxInsertAndFlushTests(
    BackendModuleWhiteboxStartWithInsertAndFlushSetup):
    def test_after_verify_triggered_reset_prior_to_removal(self):
        reason_for_backend_fail = "this is just a test, not a real failure " \
            "on verify, testing reset"
        def test_for_correct_backend_id(
            backend_mod_self, backend_id, fin_trans):
            return backend_id == self.FIRST_BACKEND_ID and \
                fin_trans == self.fin_trans
        self.backend_module.program_failure(
            VERIFY_RESET, BoKeepBackendResetException,
            reason_for_backend_fail, test_for_correct_backend_id)
        self.backend_module.mark_transaction_for_removal(self.front_end_id)
        try:
            self.backend_module.\
                _BackendModule__advance_all_dirty_transaction_state_machine()
        except BoKeepBackendResetException, reset_except:
            actions = self.backend_module.pop_actions_queue()
            self.assertEquals(len(actions), 1)
            blah = self.backend_module._BackendModule__front_end_to_back[
            self.front_end_id]
            self.assertEquals(
                blah.get_state(),
                BackendDataStateMachine.BACKEND_OUT_OF_SYNC)
            self.backend_module.\
                _BackendModule__set_all_transactions_to_reset_and_advance()
            actions = self.backend_module.pop_actions_queue()
            self.assertEquals(len(actions), 0)
        else:
            self.assert_(False)
        
  

if __name__ == "__main__":
    main()
