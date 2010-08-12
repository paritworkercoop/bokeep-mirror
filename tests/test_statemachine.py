from unittest import TestCase, main

from bokeep.util import FunctionAndDataDrivenStateMachine, \
    StateMachineMinChangeDataStore

# states in the path to the dark side
NUM_STATES = 4
(FEAR, ANGER, HATE, SUFFERING) = range(NUM_STATES)
DARK_SIDE_STRINGS = ('Fear is the path to the dark side.', # FEAR
                     'Fear leads to anger.',               # ANGER
                     'Anger leads to hate.',               # HATE
                     'Hate leads to suffering.',           # SUFFERING
                     )
assert( len(DARK_SIDE_STRINGS) == NUM_STATES )
                     
def string_for_state(state_machine, new_state):
    return DARK_SIDE_STRINGS[new_state]

class StateMachineTest(TestCase):
    def setUp(self):
        dark_side_transitions = (
            ( (self.enough_fear_to_transition,
               string_for_state, ANGER), ), # FEAR
            ( (self.enough_fear_to_transition,
               string_for_state, HATE), ), # ANGER
            ( (self.enough_fear_to_transition,
               string_for_state, SUFFERING), ), # HATE
            ( (self.enough_fear_to_transition,
               string_for_state, SUFFERING), ), # SUFFERING
            )
            
        self.assertEquals(len(dark_side_transitions),  NUM_STATES )
        self.dark_side_path = FunctionAndDataDrivenStateMachine(
            transition_table=dark_side_transitions
            )
        self.fear = 0
    
    def enough_fear_to_transition(self, state_machine, next_state):
        return self.fear / 5 > state_machine.state

    def test_direct_to_darkness(self):
        self.fear = 20
        self.dark_side_path.run_until_steady_state()
        self.assertEquals( self.dark_side_path.state, SUFFERING )

    def test_strait_up_transition_to_darkness(self):
        self.fear = 20
        self.assertEquals( self.dark_side_path.state, FEAR )
        self.dark_side_path.advance_state_machine()
        self.assertEquals( self.dark_side_path.state, ANGER )
        self.dark_side_path.advance_state_machine()
        self.assertEquals( self.dark_side_path.state, HATE )
        self.dark_side_path.advance_state_machine()
        self.assertEquals( self.dark_side_path.state, SUFFERING )
        self.dark_side_path.advance_state_machine()
        self.assertEquals( self.dark_side_path.state, SUFFERING )

    def test_stuck_in_gear(self):
        self.assertEquals( self.dark_side_path.state, FEAR )
        self.dark_side_path.advance_state_machine()
        self.assertEquals( self.dark_side_path.state, FEAR )
        self.fear = 5
        self.assertEquals( self.dark_side_path.state, FEAR )
        self.dark_side_path.advance_state_machine()
        self.assertEquals( self.dark_side_path.state, ANGER )
        self.dark_side_path.advance_state_machine()
        self.assertEquals( self.dark_side_path.state, ANGER )
        self.dark_side_path.advance_state_machine()
        self.assertEquals( self.dark_side_path.state, ANGER )

class StateMachineMinChangeDataStoreTest(TestCase):
    def setUp(self):
        dark_side_transitions = (
            ( (self.enough_fear_to_transition,
               self.revise_string_and_fear_magnified, ANGER), ), # FEAR
            ( (self.enough_fear_to_transition,
               self.revise_string_and_fear_magnified, HATE), ), # ANGER
            ( (self.enough_fear_to_transition,
               self.revise_string_and_fear_magnified, SUFFERING), ), # HATE
            ( (self.enough_fear_to_transition,
               self.revise_string_and_fear_magnified, SUFFERING), ), # SUFFERING
            )
            
        self.assertEquals(len(dark_side_transitions),  NUM_STATES )
        self.dark_side_path = FunctionAndDataDrivenStateMachine(
            transition_table=dark_side_transitions,
            data=StateMachineMinChangeDataStore(fear_string=None,
                                                fear_magnified=0,
                                                yoda_points=12,
                                                gods_number=3)
            )
        self.fear = 0

    def revise_string_and_fear_magnified(self, state_machine, new_state):
        return state_machine.data.duplicate_and_change(
            fear_string=DARK_SIDE_STRINGS[new_state],
            fear_magnified=self.fear * (2 ** new_state))

    def test_fear_magnified(self):
        self.fear = 20
        self.assertEquals( self.dark_side_path.state, FEAR )
        self.dark_side_path.advance_state_machine()
        self.assertEquals( self.dark_side_path.state, ANGER )
        self.assertEquals( self.dark_side_path.data.get_value('fear_magnified'),
                           40)

    def enough_fear_to_transition(self, state_machine, next_state):
        return self.fear / 5 > state_machine.state

if __name__ == "__main__":
    main()
