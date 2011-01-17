from unittest import TestCase, main

from bokeep.gui.state import \
    BoKeepGuiState, \
    NEW, DELETE, FORWARD, BACKWARD, TYPE_CHANGE, BOOK_CHANGE, CLOSE, RESET
from bokeep.book import BoKeepBook

class GuiTestBasicSetup(TestCase):
    def setUp(self):
        self.state = BoKeepGuiState()

def make_action_allow_or_not(action, allow=True):
    def test_fn(self):
        self.assertEquals(self.state.action_allowed(action), allow)
    return test_fn

def make_state_transid_tester(expect=None):
    def test_fn(self):
        self.assertEquals(expect, self.state.get_transaction_id())
    return test_fn

class GuiTestBasicTests(GuiTestBasicSetup):
    test_new_not_allowed = make_action_allow_or_not(NEW, False)
    test_del_not_allowed = make_action_allow_or_not(DELETE, False)
    test_forward_not_allowed = make_action_allow_or_not(FORWARD, False)
    test_backward_not_allowed = make_action_allow_or_not(BACKWARD, False)
    test_ty_change_not_allowed = make_action_allow_or_not(
        TYPE_CHANGE, False)
    test_book_change_allowed = make_action_allow_or_not(BOOK_CHANGE)
    test_close_change_allowed = make_action_allow_or_not(CLOSE)

    test_transid_none = make_state_transid_tester()

class GuiTestBasicTestsAfterClose(GuiTestBasicTests):
    def setUp(self):
        super(GuiTestBasicTestsAfterClose, self).setUp()
        self.state.do_action(CLOSE)

TESTBOOK = 'testbook'
class GuiTestWithBookSetup(GuiTestBasicSetup):
    def setUp(self):
        super(GuiTestWithBookSetup, self).setUp()
        self.book = BoKeepBook(TESTBOOK)
        self.state.do_action(BOOK_CHANGE, self.book)

class GuiTestWithBook(GuiTestWithBookSetup):
    test_new_not_allowed = make_action_allow_or_not(NEW, False)
    test_del_not_allowed = make_action_allow_or_not(DELETE, False)
    test_forward_not_allowed = make_action_allow_or_not(FORWARD, False)
    test_backward_not_allowed = make_action_allow_or_not(BACKWARD, False)
    test_ty_change_not_allowed = make_action_allow_or_not(
        TYPE_CHANGE, False)
    test_book_change_allowed = make_action_allow_or_not(BOOK_CHANGE)
    test_close_change_allowed = make_action_allow_or_not(CLOSE)

    test_transid_none = make_state_transid_tester()

TEST_MODULE='tests.test_transaction_and_module'
class GuiTestWithBookAndAvailableTypesSetup(GuiTestWithBookSetup):
    def setUp(self):
        super(GuiTestWithBookAndAvailableTypesSetup, self).setUp()
        self.book.add_module(TEST_MODULE)
        self.book.enable_module(TEST_MODULE)
                                            

class GuiTestWithBookAndAvailableTypes(
    GuiTestWithBookAndAvailableTypesSetup):
    test_new_allowed = make_action_allow_or_not(NEW)
    test_del_not_allowed = make_action_allow_or_not(DELETE, False)
    test_forward_not_allowed = make_action_allow_or_not(FORWARD, False)
    test_backward_not_allowed = make_action_allow_or_not(BACKWARD, False)
    test_ty_change_not_allowed = make_action_allow_or_not(
        TYPE_CHANGE, False)
    test_book_change_allowed = make_action_allow_or_not(BOOK_CHANGE)
    test_close_change_allowed = make_action_allow_or_not(CLOSE)
    test_transid_none = make_state_transid_tester()

FIRST_TRANS_ID = 0
                                                
class GuiTestWithFirstNewTransSetup(
    GuiTestWithBookAndAvailableTypesSetup):
    def setUp(self):
        super(GuiTestWithFirstNewTransSetup, self).setUp()
        self.state.do_action(NEW)

class GuiTestWithFirstNewTrans(GuiTestWithFirstNewTransSetup):
    test_new_allowed = make_action_allow_or_not(NEW)
    test_del_allowed = make_action_allow_or_not(DELETE)
    test_forward_not_allowed = make_action_allow_or_not(FORWARD, False)
    test_backward_not_allowed = make_action_allow_or_not(BACKWARD, False)
    test_ty_change_allowed = make_action_allow_or_not(TYPE_CHANGE)
    test_book_change_allowed = make_action_allow_or_not(BOOK_CHANGE)
    test_close_change_allowed = make_action_allow_or_not(CLOSE)

    test_transid_none = make_state_transid_tester(FIRST_TRANS_ID)


    def test_type_change(self):
        self.state.do_action(TYPE_CHANGE, 1)

    def test_bad_type_change(self):
        self.assertRaises(AssertionError, self.state.do_action,
                          TYPE_CHANGE)

    def test_reset_after_remove(self):
        self.assertEquals(self.state.get_transaction_id(), FIRST_TRANS_ID)
        self.book.remove_transaction(FIRST_TRANS_ID)
        self.state.do_action(RESET)
        self.assertEquals(self.state.get_transaction_id(), None)

    def test_reset_while_new(self):
        self.state.do_action(RESET)
        self.assertFalse(self.state.action_allowed(TYPE_CHANGE))

class GuiTestWithFirstNewTransInBrowseSetup(GuiTestWithFirstNewTransSetup):
    def setUp(self):
        super(GuiTestWithFirstNewTransInBrowseSetup, self).setUp()
        self.state.do_action(CLOSE)

class GuiTestWithFirstNewTransInBrowse(
    GuiTestWithFirstNewTransInBrowseSetup):

    def test_reset_after_background_remove(self):
        self.assertEquals(self.state.get_transaction_id(), FIRST_TRANS_ID)
        self.book.remove_transaction(FIRST_TRANS_ID)
        self.state.do_action(RESET)
        self.assertEquals(self.state.get_transaction_id(), None)

if __name__ == "__main__":
    main()
