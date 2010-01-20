from unittest import TestCase, main

from bokeep.util import FunctionAndDataDrivenStateMachine

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
            dark_side_transitions
            )
        self.fear = 0
    
    def enough_fear_to_transition(self, state_machine):
        return self.fear / 5 > state_machine.state

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


if __name__ == "__main__":
    main()
