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
                self.init_basicnew()
            elif state == self.BROWSING:
                self.init_browsing()


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

    def init_basicnew(self):
        print 'doing init basicnew'
        self.gui.set_back_sensitive(True)
        self.gui.set_forward_sensitive(False)
        self.gui.set_delete_sensitive(True)
        self.gui.set_transcombo_sensitive(True)
        self.gui.set_transcombo_index(0)
        self.gui.reset_trans_view()  
        self.new_trans_id = self.gui.current_transaction_id

        self.gmodule.set_state(self.BASIC_NEW_TRANSACTION)
      
    def init_browsing(self):
        print 'doing init browsing'
        self.gui.set_delete_sensitive(True)
        self.gui.set_transcombo_sensitive(False)
#        self.gui.reset_trans_view()  

        loc = self.gmodule.get_trans_location() 

        if loc == None:
            print 'going to latest'
            self.gui.load_latest_transaction()
        else:
            print 'going to ' + str(loc)
            self.gui.browse_to_transaction(loc)

        self.gmodule.set_state(self.BROWSING)

    def notrans_to_startup(self, *args):
        self.init_startup()
  
    def check_startup_to_basicnew(self, *args):
        if self.gui.new_requested:
            return True
        else:
            return False

    def startup_to_basicnew(self, *args):
        self.init_basicnew()

    def check_basicnew_to_basicnew(self, *args):
        if self.gui.new_requested and self.gui.new_trans_id == None:
            return True
        else:
            return False

    def basicnew_to_basicnew(self, *args):
        self.init_basicnew()

    def check_basicnew_to_browsing(self, *args):    
        #if we're still editing, don't go to browsing
        if self.gui.new_requested:
            return False
        else:
            return True

    def basicnew_to_browsing(self, *args):
        self.init_browsing()

    def check_browsing_to_notrans(self, *args):
        # where is the boolean return? probaly not written
        # yet due to no need for delete suport
        print 'check_browsing_to_notrans with ' + str(args)

    def browsing_to_notrans(self, *args):
        print 'browsing_to_notrans with ' + str(args)

    def check_browsing_to_basicnew(self, *args):
        if self.gui.new_requested:
            return True
        else:
            return False

    def browsing_to_basicnew(self, *args):
        self.init_basicnew()

class BoKeepGuiState(Persistent):
    def __init__(self, init_state=GuiStateMachine.UNKNOWN):
        super(BoKeepGuiState, self).__init__()
        self.current_state = init_state
        self.trans_location = None
        self.current_book_name = None
    
    @ends_with_commit
    def set_state(self, state):
        self.current_state = state

    @ends_with_commit
    def set_trans_location(self, location):
        self.trans_location = location       

    @ends_with_commit
    def set_book_name(self, book):
        self.current_book_name = book

    def get_state(self):
        return self.current_state

    def get_trans_location(self):
        return self.trans_location

    def get_book_name(self):
        return self.current_book_name
