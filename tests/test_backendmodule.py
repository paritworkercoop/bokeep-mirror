import os
import glob

from unittest import TestCase, main
from decimal import Decimal
from itertools import chain

from bokeep.backend_modules.module import BackendModule
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

    def look_for_save(self):
        actions = self.backend_module.pop_actions_queue()
        self.assertEquals(len(actions), 1)
        self.assertEquals(actions.pop()[0], SAVE)

class BasicBackendModuleTest(BackendModuleBasicSetup):
    def test_null_reset(self):
        # hmm, still saves even if no changes, might want to change that
        # someday
        self.backend_module.flush_backend()
        self.look_for_save()

class StartWithInsertSetup(BackendModuleBasicSetup):
    def setUp(self):
        BackendModuleBasicSetup.setUp(self)
        self.front_end_id = 0
        self.backend_module.mark_transaction_dirty(
            self.front_end_id, self.transaction)


class StartWithInsertTest(StartWithInsertSetup):
    def test_transaction_create_and_remove(self):
        self.backend_module.flush_backend()
        actions = self.backend_module.pop_actions_queue()
        self.assertEquals(len(actions), 2)

        action1 = actions.pop()
        self.assertEquals(len(action1), 3)
        cmd, return_val, transaction = action1
        self.assertEquals(cmd, CREATE)
        self.assertEquals(return_val, 1)
        self.assertEquals(transaction,
                          self.transaction.get_financial_transactions()[0])
        
        action2 = actions.pop()
        self.assertEquals(len(action2), 2)
        cmd, return_val = action2
        self.assertEquals(cmd, SAVE)
        self.assertEquals(return_val, None)

        self.backend_module.flush_backend()
        self.look_for_save()

        self.backend_module.mark_transaction_dirty(
            self.front_end_id, self.transaction)
        self.backend_module.flush_backend()
        actions = self.backend_module.pop_actions_queue()
        self.assertEquals(len(actions), 4) # verify, remove, create, save

        action1 = actions.pop()
        self.assertEquals(len(action1), 4)
        cmd, return_val, backend_ident, fin_trans = action1
        self.assertEquals(cmd, VERIFY)       
        self.assertEquals(return_val, True)
        self.assertEquals(backend_ident, 1)
        self.assertEquals(fin_trans,
                          self.transaction.get_financial_transactions()[0] )

        action2 = actions.pop()
        self.assertEquals(len(action2), 3)
        cmd, return_val, backend_ident = action2
        self.assertEquals(cmd, REMOVE)
        self.assertEquals(return_val, None)
        self.assertEquals(backend_ident, 1)

        action3 = actions.pop()
        self.assertEquals(len(action3), 3)
        cmd, return_val, transaction = action3
        self.assertEquals(cmd, CREATE)
        self.assertEquals(return_val, 2)
        self.assertEquals(transaction,
                          self.transaction.get_financial_transactions()[0])

if __name__ == "__main__":
    main()
