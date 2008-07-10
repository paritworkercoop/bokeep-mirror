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

class ThreadEndMessage(ThreadAccessingMessage):
    def handle_message(self):
        self.runing_thread.set_stop_running_flag()
        

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
        self.trans_wait_list.append( ThreadEndMessage(self) )

    def end_thread_and_join(self):
        self.request_thread_end()
        self.join()
    
    @changelock
    def continue_running(self):
        return self.__continue_running

    @changelock
    def set_stop_running_flag(self):
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

    def wait_lists_switched(active_message_list, empty_list):
        """Called right after the message lists are switched with the two
        lists, but before the lock is given up.
        """
        pass

    def message_block_begin(self):
        pass

    def message_block_end(self):
        pass

