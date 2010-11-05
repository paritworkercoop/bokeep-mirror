# python
from unittest import TestCase, main

# bo-keep
from bokeep.gui.state import \
    BoKeepGuiState, \
    NEW, DELETE, FORWARD, BACKWARD, TYPE_CHANGE, BOOK_CHANGE, CLOSE

from test_bokeep_book import BoKeepWithBookSetup
from test_gnucash24_backend import GnuCash24BasicSetup

TRUST_PLUGIN = 'bokeep.plugins.trust'
TEST_TRUSTOR = 'testtrustor'

BACKEND_PLUGIN = 'bokeep.backend_plugins.gnucash_backend24'

class BoKeepFullStackTest(BoKeepWithBookSetup, GnuCash24BasicSetup):
    def setUp(self):
        BoKeepWithBookSetup.setUp(self)
        
        # set up the trust plugin
        self.test_book_1.add_module(TRUST_PLUGIN)
        self.test_book_1.enable_module(TRUST_PLUGIN)
        self.trust_plugin = self.test_book_1.get_module(TRUST_PLUGIN)
        self.trust_plugin.add_trustor_by_name(TEST_TRUSTOR)

        # set up GnuCash backend plugin
        GnuCash24BasicSetup.setUp(self)
        self.backend_module.close()
        self.test_book_1.set_backend_module(BACKEND_PLUGIN)
        self.backend_module = self.test_book_1.get_backend_module()
        self.backend_module.setattr(
            'gnucash_file', self.get_gnucash_file_name_with_protocol() )
        
        # set up the gui state
        self.state = BoKeepGuiState()
        self.state.do_action(BOOK_CHANGE, self.test_book_1)

    def test_mu(self):
        pass

    def tearDown(self):
        self.state.do_action(CLOSE)
        GnuCash24BasicSetup.tearDown(self)
        BoKeepWithBookSetup.tearDown(self)

if __name__ == "__main__":
    main()
