import os
import glob

from unittest import TestCase, main
from decimal import Decimal
from itertools import chain

from bokeep.backend_modules.module import BackendModule, BoKeepBackendException
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

REMOVE, CREATE, VERIFY, SAVE, CLOSE = range(5)

def create_logging_function(func, cmd):
    def logging_function(self, *args):
        return_value = func(self, *args)
        self.actions_queue.append(tuple( chain(
                    (cmd,), (return_value,), args) ) )
        return return_value
    return logging_function

null_function = lambda *args: None

class BackendModuleUnitTest(BackendModule):
    def __init__(self):
        BackendModule.__init__(self)
        self.clear_actions_queue()
        self.counter = 0
        
    def can_write(self):
        return True
    
    remove_backend_transaction = create_logging_function(null_function, REMOVE)

    def create_backend_transaction(self, fin_trans):
        self.counter+=1
        return self.counter
    create_backend_transaction = create_logging_function(
        create_backend_transaction, CREATE)

    verify_backend_transaction = create_logging_function(
        BackendModule.verify_backend_transaction, VERIFY)

    save = create_logging_function(null_function, SAVE)   
    close = create_logging_function(BackendModule.close, CLOSE)

    def pop_actions_queue(self):
        return_value = self.actions_queue
        return_value.reverse()
        self.clear_actions_queue()
        return return_value

    def clear_actions_queue(self):
        self.actions_queue = []

class BackendModuleBasicSetup(TestCase):
    """This tests that BackendModule makes calls to the subclass functions
    create_backend_transaction, remove_backend_transaction,
    verify_backend_transaction, save, and close in the expected order, and
    responded in the expected way with calls to mark_transaction_dirty,
    mark_transaction_for_removal, mark_transaction_for_verification,
    mark_transaction_for_hold, mark_transaction_for_forced_remove,
    transaction_is_clean, reason_transaction_is_dirty, flush_backend, and
    backend_reset_occured

    I'm not sure this is quite blackbox testing, but certainly not whitebox
    either, perhaps greybox?
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

    def look_for_verify(self, actions, orig_fin_trans):
        action1 = actions.pop()
        self.assertEquals(len(action1), 4)
        cmd, return_val, backend_ident, fin_trans = action1
        self.assertEquals(cmd, VERIFY)       
        self.assertEquals(return_val, True)
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

class BasicBackendModuleTest(BackendModuleBasicSetup):
    def test_null_reset(self):
        # hmm, still saves even if no changes, might want to change that
        # someday
        self.backend_module.flush_backend()
        self.pop_all_look_for_save()

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

    # not an actual test case, has to be called by a function
    # that starts with test in the name
    def run_test_of_forced_remove_of_non_held_transaction(self):
        self.assertRaises(
            BoKeepBackendException,
            self.force_remove_known_transaction)

class StartWithInsertTest(StartWithInsertSetup):
    def test_forced_remove_of_non_held_transaction(self):
        self.run_test_of_forced_remove_of_non_held_transaction()

    def test_hold_of_uncommited_new_transaction(self):
        self.backend_module.mark_transaction_for_hold(self.front_end_id)
        self.backend_module.flush_backend()
        # this should just save, in the future, we might even avoid the
        # wasted save here
        self.pop_all_look_for_save()

    def test_verify_fail_right_after_insert(self):
        self.assertRaises(
            BoKeepBackendException,
           self.backend_module.mark_transaction_for_verification,
            self.front_end_id )

    def test_re_insert_trouble_when_change(self):
        self.assertRaises(
            BoKeepBackendException,
            self.backend_module.mark_transaction_dirty,
            self.front_end_id, None
            )

    def test_remove_right_after_insert(self):
        self.backend_module.mark_transaction_for_removal(self.front_end_id)
        self.backend_module.flush_backend()
        self.pop_all_look_for_save()

    def test_create(self):
        self.backend_module.flush_backend()
        actions = self.backend_module.pop_actions_queue()
        self.look_for_create(actions, self.FIRST_BACKEND_ID, self.fin_trans )
        self.look_for_save(actions)

class StartWithInsertAndFlushSetup(StartWithInsertSetup):
    def setUp(self):
        StartWithInsertSetup.setUp(self)
        self.backend_module.flush_backend()
        self.backend_module.pop_actions_queue()
        self.SECOND_BACKEND_ID = self.FIRST_BACKEND_ID+1

class StartWithInsertAndFlushTests(StartWithInsertAndFlushSetup):
    def test_forced_remove_of_non_held_transaction(self):
        self.run_test_of_forced_remove_of_non_held_transaction()
        
    def test_transaction_verify(self):
        # this should do a VERIFY and a SAVE
        self.backend_module.mark_transaction_for_verification(
            self.front_end_id)
        self.backend_module.flush_backend()
        
        actions = self.backend_module.pop_actions_queue()
        self.assertEquals(len(actions), 2)
        self.look_for_verify(actions, self.fin_trans)
        self.look_for_save(actions)
    
    def test_multi_verify(self):
        for i in xrange(20):
            self.backend_module.mark_transaction_for_verification(
                self.front_end_id)
        self.test_transaction_verify()

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
        self.backend_module.flush_backend()

        actions = self.backend_module.pop_actions_queue()
        self.assertEquals(len(actions), 4) # verify, remove, create, save

        self.look_for_verify(actions, self.fin_trans)
        self.look_for_remove(actions, self.FIRST_BACKEND_ID)
        self.look_for_create(actions, self.SECOND_BACKEND_ID, self.fin_trans)
        self.look_for_save(actions)

    def test_transaction_remove(self):
        self.backend_module.mark_transaction_for_removal(self.front_end_id)
        self.backend_module.flush_backend()
        actions = self.backend_module.pop_actions_queue()
        self.assertEquals(len(actions), 3) # verify, remove, save
        self.look_for_verify(actions, self.fin_trans)
        self.look_for_remove(actions, self.FIRST_BACKEND_ID)
        self.look_for_save(actions)
       

class StartWithInsertFlushAndHoldSetup(StartWithInsertAndFlushSetup):
    def setUp(self):
        StartWithInsertAndFlushSetup.setUp(self)
        self.backend_module.mark_transaction_for_hold(self.front_end_id)
        self.backend_module.flush_backend()
        self.backend_module.pop_actions_queue()


class InsertFlushAndHoldTest(StartWithInsertFlushAndHoldSetup):
    def test_success_force_remove(self):
        actions = self.backend_module.pop_actions_queue()
        self.assertEquals(len(actions), 0)
        
        self.force_remove_known_transaction()
        self.backend_module.flush_backend()
        actions = self.backend_module.pop_actions_queue()
        # expecting REMOVE and SAVE
        self.assertEquals(len(actions), 2)
        self.look_for_remove(actions, self.FIRST_BACKEND_ID)
        self.look_for_save(actions)

if __name__ == "__main__":
    main()
        

