# python standard library
from threading import Thread, Condition

# ZODB
import transaction

# simplifies common ussage of transaction.get().commit()
def ends_with_commit(dec_function):
    def ret_func(*args, **kargs):
        return_value = dec_function(*args, **kargs)
        transaction.get().commit()
        return return_value
    return ret_func


# Message handling thread stuff

class Message(object):
    pass

class ThreadAccessingMessage(Message):
    def __init__(self, running_thread):
        Message.__init__(self)
        self.running_thread = running_thread    

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

class MessageRecievingThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.message_wait_list = []
        self.change_availible = Condition()
        self.__continue_running = True

    @waitlistmodify
    def request_thread_end(self):
        self.message_wait_list.append( ThreadEndMessage(self) )

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
                messsage = active_message_list.pop()
                message.handle_message()

            # active_message_list now empty
            empty_list = active_message_list

            self.message_block_end()

    def wait_list_switched(active_message_list, empty_list):
        """Called right after the message lists are switched with the two
        lists, but before the lock is given up.
        """
        pass

    def message_block_begin(self):
        pass

    def message_block_end(self):
        pass


PRIMARY_DELTA, SECONDARY_DELTA, ENTITY = range(3)

class EntityChangeMessage(ThreadCallbackMessage):
    def __init__(self, running_thread, entity_identifier):
        ThreadCallbackMessage.__init__(running_thread)
        self.entity_identifier = entity_identifier

class EntityChangeManager(EntityChangeMessage):
    callback_function = 'handle_entity_change_message'  

class EntityChangeEnd(EntityChangeMessage):
    callback_function = 'remove_delta'

def entitymod(dec_function):
    @changelock
    def ret_function(self, *args, **kargs):
        delta = self.change_manager_lookup_dict[
            (args[0], PRIMARY_DELTA) ]
        return_value = dec_function(self, delta, *args, **kargs)
        if not delta in self.message_wait_list:
            self.message_wait_list.append(delta)
            self.change_availible.notify()
        return return_value
    return ret_function

class ChangeMessageRecievingThread(MessageRecievingThread):
    def __init__(self):
        MessageReceivingThread.__init__(self)
        self.change_manager_lookup_dict = {}

    def wait_list_switched(active_message_list, empty_list):
        """Called right after the message lists are switched with the two
        lists, but before the lock is given up.
        """
        for delta in active_message_list:
            if isinstance(delta, EntityChangeManager):
                delta_keys = [ (delta.entity_identifier, x)
                               for x in (PRIMARY_DELTA, SECONDARY_DELTA) ]
                    
                secondary_delta = self.change_manager_lookup_dict[
                    delta_keys[SECONDARY_DELTA] ]
                self.change_manager_lookup_dict[
                    delta_keys[SECONDARY_DELTA] ] = \
                    self.change_manager_lookup_dict[delta_keys[PRIMARY_DELTA] ]
                self.change_manager_lookup_dict[ delta_keys[PRIMARY_DELTA] ] = \
                    secondary_delta

    @changelock
    def add_change_tracker(self, entity_identifier):
        assert( (entity_identifier, PRIMARY_DELTA) not in
                self.change_manager_lookup_dict )
        for x in (PRIMARY_DELTA, SECONDARY_DELTA):
            self.change_manager_lookup_dict[(entity_identifier, x)] = \
            EntityChangeManager(self, entity_identifier)

    @waitlistmodify
    def remove_change_tracker(self, entity_identifier):
        assert( (entity_identifier, PRIMARY_DELTA) in
                self.change_manager_lookup_dict )
        self.message_wait_list.append(
            EntityChangeEnd(self, entity_identifier) )

    @changelock
    def get_entity_for_delta(self, delta):
        entity_key = (delta.entity_identifier, ENTITY)
        if not entity_key in self.change_manager_lookup_dict:
            entity = self.get_entity_from_identifier(delta.entity_identifier)
            self.change_manager_lookup_dict[entity_key] = entity
        else:
            entity = self.change_manager_lookup_dict[entity_key]
        return entity

    def handle_entity_change_message(self, change_message):
        self.handle_entity_change(self.get_entity_for_delta(change_message) )
    
    @changelock
    def remove_delta(self, message):
        for x in (PRIMARY_DELTA, SECONDARY_DELTA, TRANSACTION):
            del self.change_manager_lookup_dict[(message.entity_identifier, x)]
        
