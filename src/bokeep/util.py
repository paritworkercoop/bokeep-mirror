# Copyright (C) 2010-2010  ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
# Copyright (C) 2011 SkullSpace Winnipeg Inc. <andrew@andreworr.ca>
#
# This file is part of Bo-Keep.
#
# Bo-Keep is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Mark Jenkins <mark@parit.ca>
# Author: Andrew Orr <andrew@andreworr.ca>

# python standard library
from threading import Thread, Condition, Event
from os.path import abspath, dirname, join, exists, basename
from datetime import date, timedelta
from zlib import adler32
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP

# ZODB
import transaction
from persistent import Persistent

# simplifies common usage of transaction.get().commit()
def ends_with_commit(dec_function):
    def ret_func(*args, **kargs):
        return_value = dec_function(*args, **kargs)
        transaction.get().commit()
        return return_value
    return ret_func

def none_args_become_dict(function):
    def new_function(*args, **kargs):
        new_args = []
        for arg in args:
            if arg == None:
                arg = {}
            new_args.append(arg)
        return function( *new_args, **kargs )
    return new_function

def attribute_or_blank(obj, attr):
    if hasattr(obj, attr):
        return getattr(obj, attr)
    else:
        return ""

# Message handling thread stuff

class Message(object):
    pass

class ThreadAccessingMessage(Message):
    def __init__(self, running_thread):
        Message.__init__(self)
        self.running_thread = running_thread    

class ThreadExecuteMessage(ThreadAccessingMessage):
    def __init__(self, running_thread, exec_procedure):
        ThreadAccessingMessage.__init__(self, running_thread)
        self.exec_procedure = exec_procedure

    def handle_message(self):
        args, kargs = self.running_thread.get_arguments_for_exec_procedure()
        self.exec_procedure( *args, **kargs )
        

class ThreadCallbackMessage(ThreadAccessingMessage):
    """Messages whoes only role in life is to make a call back to the
    thread instance, as it is more convienent to process the message
    there
    """
    def handle_message(self):
        getattr(self.running_thread, self.callback_function)(self)

class ThreadEndMessage(ThreadCallbackMessage):
    callback_function = 'set_stop_running_flag'

def changelock(dec_function):
    def ret_function(self, *args):
        self.change_availible.acquire()
        return_value = dec_function(self, *args)
        self.change_availible.release()
        return return_value
    return ret_function

def waitlistmodify(dec_function):
    @changelock
    def ret_function(self, *args):
        return_value = dec_function(self, *args)
        self.change_availible.notify()
        return return_value
    return ret_function

def waitlistappend(dec_function):
    @waitlistmodify
    def ret_function(self, *args):
        self.message_wait_list.append( dec_function(self, *args) )
    return ret_function

class MessageRecievingThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.message_wait_list = []
        self.change_availible = Condition()
        self.__continue_running = True

    @waitlistappend
    def request_thread_execute(self, exec_procedure):
        return ThreadExecuteMessage(self, exec_procecure)

    @waitlistappend
    def request_thread_end(self):
        return ThreadEndMessage(self)

    def end_thread_and_join(self):
        self.request_thread_end()
        self.join()
    
    @changelock
    def continue_running(self):
        return self.__continue_running

    @changelock
    def set_stop_running_flag(self, message):
        self.__continue_running = False

    def run(self):       
        empty_list = []

        while self.continue_running():
            self.change_availible.acquire()
            if len(self.message_wait_list) == 0:
                self.change_availible.wait()
            assert( len(self.message_wait_list) > 0 )
            
            # lock still acquired [.acquire()] or reacquired [.wait()] here
            # we quickly switch out the waiting list of messages
            # with the empty list of messages
            active_message_list = self.message_wait_list
            self.message_wait_list = empty_list
            self.wait_lists_switched(active_message_list, empty_list)
            self.change_availible.release()
            # lock released
            
            self.message_block_begin()

            # deal with everything in trans_to_handle, reverse to reflect
            # actual order of entry
            active_message_list.reverse()
            while len(active_message_list) > 0:
                message = active_message_list.pop()
                message.handle_message()

            # active_message_list now empty
            empty_list = active_message_list

            self.message_block_end()

    def wait_lists_switched(self, active_message_list, empty_list):
        """Called right after the message lists are switched with the two
        lists, but before the lock is given up.
        """
        pass

    def message_block_begin(self):
        pass

    def message_block_end(self):
        pass


class EntityChangeMessage(ThreadCallbackMessage):
    def __init__(self, running_thread, entity_identifier):
        ThreadCallbackMessage.__init__(self, running_thread)
        self.entity_identifier = entity_identifier

class EntityChangeManager(EntityChangeMessage):
    callback_function = 'handle_entity_change_message'  

class EntityChangeEnd(EntityChangeMessage):
    notify_of_end_function = None
    callback_function = 'remove_delta'

def entitymod(dec_function):
    @changelock
    def ret_function(self, *args, **kargs):
        changes = self.waiting_changes[args[0]]
        new_args = args[1:]
        return_value = dec_function(self, changes, *new_args, **kargs)
        if not args[0] in self.wait_list_change_set:
            self.message_wait_list.append(changes)
            self.wait_list_change_set.add( args[0] )
        self.change_availible.notify()
    return ret_function

class ChangeMessageRecievingThread(MessageRecievingThread):
    def __init__(self):
        MessageRecievingThread.__init__(self)
        self.changes_being_processed = {}
        self.waiting_changes = {}
        self.entity_lookup_dict = {}
        self.wait_list_change_set = set()
        # track the latest EntityChangeEnd message for a particular entity,
        # we don't care if several are in queue, just track the latest
        self.end_change_lookup_dict = {}


    def wait_lists_switched(self, active_message_list, empty_list):
        """Called right after the message lists are switched with the two
        lists, but before the lock is given up.
        """
        temp = self.changes_being_processed
        self.changes_being_processed  = self.waiting_changes
        self.waiting_changes = temp
        self.wait_list_change_set.clear()

    @changelock
    def add_change_tracker(self, entity_identifier,
                           entity_change_ready_callback):
        """Calling convention, you should call add_change_tracker for a
        particular entity only if you havn't done so yet, or if you've done
        so but ended your series of changes with remove_change_tracker()

        Callbacks must not continue executing and eventually call this back,
        or the stack will never shink. Instead, the should trigger an event
        somewhere, see add_change_tracker_block for a simple example
        """
        # if we're already tracking a particular entity, call
        # entity_change_ready_callback when the latest call to
        # remove_change_tracker has been called
        if entity_identifier in self.changes_being_processed:
            # Enforce calling convention, every call to add_change_tracker
            # must be followed by a call to remove_change_tracker
            # before you can call it again
            #
            # See that an end_change message has been inserted
            assert( entity_identifier in self.end_change_lookup_dict)
            end_msg = self.end_change_lookup_dict[entity_identifier]
            # ensure that the end_change_message hasn't been told to notify
            # that would also be a sign that the call convention is being
            # violated
            assert( end_msg.notify_of_end_function == None)
            end_msg.notify_of_end_function = entity_change_ready_callback
        # else the entity isn't already being tracked, start tracking
        else:
            # in this situation, the key should of been deleted
            assert( entity_identifier not in self.end_change_lookup_dict)
            for dictionary in \
                    (self.changes_being_processed, self.waiting_changes):
                dictionary[entity_identifier] = \
                    self.new_entity_change_manager(entity_identifier)
            # use the callback to inform
            entity_change_ready_callback(entity_identifier)

    def new_entity_change_manager(self, entity_identifier):
        return EntityChangeManager( self, entity_identifier)

    def add_change_tracker_block(self, entity_identifier):
        block_in_place = Event()
        def remove_blocking_condition(entity_identifier):
            block_in_place.set()
        self.add_change_tracker(entity_identifier, remove_blocking_condition)
        block_in_place.wait()

    @waitlistmodify
    def remove_change_tracker(self, entity_identifier):
        assert( entity_identifier in self.changes_being_processed )
        new_end_change_msg = EntityChangeEnd(self, entity_identifier)
        self.message_wait_list.append(new_end_change_msg)
        self.end_change_lookup_dict[entity_identifier] = new_end_change_msg
            

    @changelock
    def get_entity_for_delta(self, delta):
        entity_key = delta.entity_identifier
        if not entity_key in self.entity_lookup_dict:
            entity = self.get_entity_from_identifier(delta.entity_identifier)
            self.entity_lookup_dict[entity_key] = entity
        else:
            entity = self.entity_lookup_dict[entity_key]
        return entity

    def handle_entity_change_message(self, change_message):
        self.handle_entity_change(change_message,
                                  self.get_entity_for_delta(change_message) )
    
    @changelock
    def remove_delta(self, message):
        entity_key = message.entity_identifier
        # if we were asked to notify that things had ended,
        # we don't need to pull anything out, just notify
        if message.notify_of_end_function != None:
            message.notify_of_end_function(entity_key)
        # else remove the deltas, they're no longer neede
        else:
            for dictionary in (self.changes_being_processed,
            self.waiting_changes):
                del dictionary[entity_key]
            if entity_key in self.entity_lookup_dict:
                del self.entity_lookup_dict[entity_key]

        # if this message is the latest end message, we no lnoger need to
        # track for this entity anymore, else, leave this so others can
        # hook into this
        if self.end_change_lookup_dict[message.entity_identifier] == message:
            del self.end_change_lookup_dict[message.entity_identifier]

class FunctionAndDataDrivenStateMachine(Persistent):
    """A state machine where posible transitions are tested by boolean
    functions and followed up by transition functions, and a piece of
    data is kept at all times and altered during each transition.

    States are identified by sequential integers starting at zero

    When you call init, you provide the argument transition_rules_for_states.
    This is the table of transition rules.

    The outer level is a tuple, each element of the tuple is rules
    for leaving each particular state. For example,
    transition_rules_for_states[0] is rules for leaving state 0.

    Each set of rules is also a tuple (middle level). Each rule is
    considered, in order until a matching rule is found, subsequent
    rules are not considered. So, for example,
    transition_rules_for_states[2][0] is the first rule considered
    for leaving state 2, transition_rules_for_states[2][1] is the
    second rule considered for leaving state 2 and so on.

    The rules themselves are tuples as well. (inner level).
    They consist of a function for checking if a transition should be made,
    a function to be executed if the transition is made, and the next state
    (condition_func, transition_func, next_state) = rule
    The function condition_func is passed the state machine and the
    possible next state. If condition_func returns True, the rule is
    considered a match, a transition is made to the next state,
    and subsequent rules are not considered. On transition,
    the transition function is called with the state machine, and the
    new state. Whatever it returns will be put in the data field.

    So, that's three different levels of nested tuple,
    the outer level (state table), the middle level (rule list per state),
    and inner level (rule).

    The current state and data are always available via the data
    and state properties, or the get_data and get_state functions.
    You can not change them directly, only a state transition can do that.

    Calling advance_state_machine() triggers the tests for the current state.

    You may find the example in tests/test_statemachine.py amusing.
    """

    def __init__(
        self,
        transition_function=None,
        initial_state=0,
        data=None, transition_table=None):
        """Initialize with transition rules for each state, and optionally
        include the initial state (default 0) or data (default None).
        """
        Persistent.__init__(self)
        if transition_function != None:
            self.transition_function = transition_function
        self.__transition_table = transition_table
        self.__data = data
        self.__state = initial_state

    def get_data(self):
        return self.__data

    data = property(get_data)

    def get_state(self):
        return self.__state

    state = property(get_state)
    
    def next_state_and_data_from_table(self):
        new_state = self.__state
        new_data = self.__data
        table = self.get_table()
        for i, (condition_func, transition_func, pos_new_state) in enumerate(
            table[self.__state]):
            if condition_func(self, pos_new_state):
                new_state = pos_new_state
                new_data = transition_func(self, new_state)
                break
        return (new_state, new_data)
    
    def get_table(self):
        return self.__transition_table

    table = property(get_table)

    def transition_function(self):
        return self.next_state_and_data_from_table()

    def advance_state_machine(self):
        self.__state, self.__data = self.transition_function()

    def run_until_steady_state(self):
        old_state = None
        while old_state != self.state:
            old_state = self.state
            self.advance_state_machine()

    @staticmethod
    def make_action_check_function(action):
        def check_function(self, next_state):
            if hasattr(self, "_v_last_action"):
                result = self._v_last_action == action
                if result:
                    delattr(self, "_v_last_action")
                    return result
                else: return False
        return check_function

    @ends_with_commit
    def do_action(self, action, arg=None):
        assert( self.action_allowed(action) )
        self._v_action_arg = arg
        self._v_last_action = action
        self.run_until_steady_state()
        delattr(self, '_v_action_arg')

def state_machine_always_true(state_machine, next_state):
    return True

def state_machine_do_nothing(state_machine, next_state):
    return state_machine.data

class StateMachineMinChangeDataStore(object):
    def __init__(self, **kargs):
        # intentionaly not readable by outside world
        self.__values = kargs

    def duplicate_and_change(self, **kargs):
        new_args = self.__values
        for key, value in kargs.iteritems():
            new_args[key] = value
        return StateMachineMinChangeDataStore(**new_args)


    def get_value(self, key):
        return self.__values[key]

def enhance_syspath_for_module_load(path, position=0):
    import sys
    directory = dirname(abspath(path))
    filename = basename(path)
    sys.path.insert(position, directory)

def drop_syspath_enhancement(position=0):
    import sys
    sys.path.pop(position) # cleanup

def get_module_for_file_path(path):
    PATH_MOD_POSITION = 0
    # The're got to be a nicer way to load code from a file...
    import sys
    PYTHON_EXTENSION = ".py"
    if not path.endswith(PYTHON_EXTENSION) or not exists(path):
        return None
    directory = dirname(abspath(path))
    filename = basename(path)
    assert( filename.endswith(PYTHON_EXTENSION) )
    sys.path.insert(PATH_MOD_POSITION, directory)
    modulename = filename[:-3] # everything but last three characterrs
    try:
        return_value = __import__(modulename,  globals(), locals(), [""])
    except ImportError:
        return_value = None
    finally:
        drop_syspath_enhancement(PATH_MOD_POSITION)
    return return_value

def reload_module_at_filepath(module, path):
    enhance_syspath_for_module_load(path)
    reload(module)
    drop_syspath_enhancement()

class PluginSet(Persistent):
    def __init__(self):
        self.enabled_plugins = {}
        self.disabled_plugins = {}

    def add_plugin(self, plugin_name):
        assert( plugin_name not in self.enabled_plugins and 
                plugin_name not in self.disabled_plugins )
        # get the plugin class and instantiate as a new disabled plugin
        self.disabled_plugins[plugin_name] =  __import__(
            plugin_name, globals(), locals(), [""]).get_plugin_class()()
        self._p_changed = True

    def enable_plugin(self, plugin_name):
        assert( plugin_name in self.disabled_plugins )
        self.enabled_plugins[plugin_name] = self.disabled_plugins[plugin_name]
        del self.disabled_plugins[plugin_name]
        self._p_changed = True
        
    def disable_plugin(self, plugin_name):
        assert( plugin_name in self.enabled_plugins )
        self.disabled_plugins[plugin_name] = self.enabled_plugins[plugin_name]
        del self.enabled_plugins[plugin_name]
        self._p_changed = True

    def get_plugin(self, plugin_name):
        return self.enabled_plugins[plugin_name]

    def get_plugins(self):
        return self.enabled_plugins

    def has_plugin_enabled(self, plugin_name):
        return plugin_name in self.enabled_plugins

    def has_plugin_disabled(self, plugin_name):
        return plugin_name in self.disabled_plugins

    def has_plugin(self, plugin_name):
        return \
            self.has_plugin_enabled(plugin_name) or \
            self.has_plugin_disabled(plugin_name)

def get_file_in_same_dir_as_module(module, filename): 
    return join( dirname( abspath( module.__file__ ) ),
                 filename )

def first_of(a_date):
    return date(a_date.year, a_date.month, 1)

def last_of_month(a_date):
    return month_delta(first_of(a_date), 1) - timedelta(days=1)

def month_delta(current_date, months=1):
    """Always call with a day that is between 1 and 28, other dates can
    be invalid for shifting by month
    """
    assert( 1<= current_date.day <=28 )
    new_month = current_date.month + months
    new_year = current_date.year
    if new_month > 12 or new_month >= 0:
        # FIXME
        # this could use some heavy testing...
        new_year+= (new_month-1) / 12
        new_month = ((new_month-1) % 12) + 1
    return date(new_year, new_month, current_date.day)


def start_of_year(a_date):
    return date(a_date.year, 1, 1)

def adler32_of_file(file_path):
    """Very fast for file comparison, but a super poor choice if
    used for cyrptographic uses -- and you thought md5 sucked...
    """
    f = file(file_path)
    return_value = adler32(''.join(f)) & 0xffffffff
    f.close()
    return return_value

def get_and_establish_attribute(obj, attr, default_cls, *args, **kargs):
    return_attr = getattr(obj, attr,
                          default_cls(*args, **kargs) )
    setattr(obj, attr, return_attr )
    return return_attr

def null_function(*args, **kargs): pass

# useful with Decimal.quantize
TWOPLACES = Decimal('0.01')
ZEROPLACES = Decimal('1.')

def decimal_round_two_place_using_third_digit(decimal_value):
    # we want these results eh?
    # >>> Decimal('0.025').quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
    # Decimal("0.03")
    # >>> Decimal('0.015').quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
    # Decimal("0.02")
    # >>> Decimal('-0.015').quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
    # Decimal("-0.02")
    # >>> Decimal('-0.025').quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
    # Decimal("-0.03")
    #
    # and this
    # >>> Decimal('0.02499999999999999').quantize(Decimal('0.00'),
    #  rounding=ROUND_HALF_UP)
    # Decimal("0.02")
    #
    # Not this
    # >>> Decimal('0.02499999999999999').quantize(Decimal('0.00'),
    # rounding=ROUND_UP)
    # Decimal("0.03")

    return decimal_value.quantize(TWOPLACES, ROUND_HALF_UP)

def decimal_truncate_two_places(decimal_value):
    """ round something like 0.019 to 0.01 and -0.019 to -0.01
    """
    # note that using ROUND_FLOOR wouldn't achieve the desired results
    # with negative numbers
    return decimal_value.quantize(TWOPLACES, rounding=ROUND_DOWN)

def tup_chain(*args):
    return tuple(chain(*args))

def tup_multi_append(original_tuple, *args):
    return tup_chain(original_tuple, args)
