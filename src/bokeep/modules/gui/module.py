from persistent import Persistent
from bokeep.util import ends_with_commit
from bokeep.util import FunctionAndDataDrivenStateMachine

class GuiStateMachine(FunctionAndDataDrivenStateMachine):
    NUM_STATES = 5

     #unknown state is used when the gui module is first run.  We don't 
     #initialize it to no_transactions because there might BE transactions.  
     #Specifically, the gui module might be installed on a system that's 
     #already been running, or, that module might have gotten smashed somehow 
     #and needs reinitialization on a system that was already running.
    (UNKNOWN, NO_TRANSACTIONS, STARTUP_TRANSACTION, BASIC_NEW_TRANSACTION, BROWSING) = range(NUM_STATES)

    def check_unknown_to_startup(self, *args):
        if not self.gui.has_transactions() or self.gui.transaction_count() == 1:
            return True
        else:
            return False

    def unknown_to_startup(self, *args):
        self.init_startup()

    def check_unknown_to_browsing(self, *args):
        if self.gui.has_transactions() and self.gui.transaction_count() > 1:
            return True
        else:
            return False

    def unknown_to_browsing(self, *args):
        self.init_browsing()
    
    def init_notrans(self):
        self.gui.set_back_sensitive(False)
        self.gui.set_forward_sensitive(False)
        self.gui.set_delete_sensitive(False)
        self.gui.set_transcombo_sensitive(False)
        self.gmodule.set_state(self.NO_TRANSACTIONS)

    def check_notrans_to_startup(self, *args):
       return True

    def init_startup(self):
        print 'doing init startup'
        self.gui.set_back_sensitive(False)
        self.gui.set_forward_sensitive(False)
        self.gui.set_delete_sensitive(False)
        self.gui.set_transcombo_sensitive(True)

        if self.gui.has_transactions():
            #we have a "starting" transaction, go into editing for it      
            print 'doing load latest'
            self.gui.load_latest_transaction()
        else:
            #we have no "starting" transaction, get things rolling for it
            print 'doing start new'
            self.gui.set_transcombo_index(0)
            self.gui.reset_trans_view()

        self.gmodule.set_state(self.STARTUP_TRANSACTION)

    def init_newtrans(self):
        pass
      
    def init_browsing(self):
        pass

    def notrans_to_startup(self, *args):
        self.init_startup()
  
    def check_startup_to_basicnew(self, *args):
        print 'check_startup_to_basicnew with ' + str(args)

    def startup_to_basicnew(self, *args):
        print 'startup_to_basicnew with ' + str(args)

    def check_basicnew_to_basicnew(self, *args):
        print 'check_basicnew_to_basicnew with ' + str(args)

    def basicnew_to_basicnew(self, *args):
        print 'basicnew_to_basicnew with ' + str(args)

    def check_basicnew_to_browsing(self, *args):
        print 'check_basicnew_to_browsing with ' + str(args)

    def basicnew_to_browsing(self, *args):
        print 'basicnew_to_browsing with ' + str(args)

    def check_browsing_to_notrans(self, *args):
        print 'check_browsing_to_notrans with ' + str(args)

    def browsing_to_notrans(self, *args):
        print 'browsing_to_notrans with ' + str(args)

    def check_browsing_to_basicnew(self, *args):
        print 'check_browsing_to_basicnew with ' + str(args)

    def browsing_to_basicnew(self, *args):
        print 'browsing_to_basicnew with ' + str(args)

    def __init__(self, state, gui, gmodule):
        state_transitions = (
            #UNKNOWN
            ( (self.check_unknown_to_startup,
               self.unknown_to_startup, self.STARTUP_TRANSACTION),
              (self.check_unknown_to_browsing,
               self.unknown_to_browsing, self.BROWSING ), 
            ),

            #NO_TRANSACTIONS
            ( (self.check_notrans_to_startup,
               self.notrans_to_startup, self.STARTUP_TRANSACTION),
            ),
        
            #STARTUP_TRANSACTION
            ( (self.check_startup_to_basicnew,
               self.startup_to_basicnew, self.BASIC_NEW_TRANSACTION),
            ),
   
            #BASIC_NEW_TRANSACTION
            ( (self.check_basicnew_to_basicnew,
               self.basicnew_to_basicnew, self.BASIC_NEW_TRANSACTION), 
              (self.check_basicnew_to_browsing,
               self.basicnew_to_browsing, self.BROWSING),
            ), 
     
            #BROWSING
            ( (self.check_browsing_to_notrans,
               self.browsing_to_notrans, self.NO_TRANSACTIONS), 
              (self.check_browsing_to_basicnew,
               self.browsing_to_basicnew, self.BASIC_NEW_TRANSACTION),
            ), 

            )

        super(GuiStateMachine, self).__init__(None, state, None, state_transitions)
        self.gui = gui
        self.gmodule = gmodule

        #if we start out with a state, do the initialization associated with that state.
        if not state == None:
            if state == self.NO_TRANSACTIONS:
                self.init_notrans()
            elif state == self.STARTUP_TRANSACTION:
                self.init_startup()
            elif state == self.BASIC_NEW_TRANSACTION:
                self.init_newtrans()
            elif state == self.BROWSING:
                self.init_browsing()

class GuiModule(Persistent):

    @ends_with_commit
    def set_state(self, state):
        self.current_state = state
        self._p_changed = True

    @ends_with_commit
    def set_trans_location(self, location):
        self.trans_location = location       
        self._p_changed = True

    def get_state(self):
        if hasattr(self, "current_state"):
            return self.current_state
        else:
            return None

    def get_trans_location(self):
        if hasattr(self, "trans_location"):
            return self.trans_location
        else:
            return None

    @staticmethod
    def get_transaction_type_codes():
        return []

    @staticmethod
    def get_transaction_type_from_code(code):
        return None 

    @staticmethod
    def get_transaction_type_pulldown_string_from_code(code):
        return None
        
    @staticmethod
    def get_transaction_edit_interface_hook_from_code(code):
        return None

    @staticmethod
    def get_transaction_view_interface_hook_fom_code(code):
        return None

    @staticmethod
    def get_transaction_edit_interface_hook_from_type(ty):
        return None

    @staticmethod
    def get_transaction_view_interface_hook_from_type(ty):
        return None
    
    @staticmethod
    def get_transaction_code_from_type(ty):
        return None

