# Copyright (C) 2010  ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
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
from persistent import Persistent

from bokeep.book_transaction import \
    BoKeepTransactionNotMappableToFinancialTransaction

from bokeep.util import \
    ChangeMessageRecievingThread, EntityChangeManager, entitymod, \
    ends_with_commit, FunctionAndDataDrivenStateMachine, \
    state_machine_do_nothing, state_machine_always_true, \
    StateMachineMinChangeDataStore

import transaction

class BackendChangeManager(EntityChangeManager):
    def __init__(self, running_thread, entity_identifier):
        EntityChangeManager.__init__(self, running_thread, entity_identifier)
        self.transaction_dirty_count = 0

    def increment(self):
        self.transaction_dirty_count += 1
    
    def send_to_zero(self):
        return_value = self.transaction_dirty_count
        self.transaction_dirty_count = 0
        return return_value
 

class BackendChangeThread(ChangeMessageRecievingThread):
    
    @entitymod
    def mark_transaction_dirty(self, change_manager, entity_identifier):
        change_manager.increment()

    def get_entity_from_identifier(self, entity_identifier):
        pass

    def handle_entity_change(self, change_message, entity):
        # change required, only do this if backend is co-operative, if it
        # is locked or something ,imform other that it is still dirty
        # I wonder if we can avoid this...
        count_down = change_message.send_to_zero()
        
        # put representation of entity identified by
        # change_message.entity_identifier, and old backend id
        # to backend, receie returned backenend id and store
        #
        # send count_down back to the backend module dirty db, or nothing

class BackendModule(Persistent):
    """Illustrates the Bo-Keep backend module API

    A Bo-Keep backend module does not need to be a subclass of
    bokeep.backend_modules.module.BackendModule, but it must implement the
    following functions shown here:
    mark_transaction_dirty, mark_transaction_for_removal,
    mark_transaction_for_verification, mark_transaction_for_hold,
    mark_transaction_for_forced_remove, transaction_is_clean,
    reason_transaction_is_dirty, flush_backend, close
    update_trans_flush_check_and_close, 
    remove_trans_flush_check_and_close,
    verify_trans_and_close, setattr
    
    Many backend modules are easier to implement if you do choose to
    subclass BackendModule, and just implemnt functions such as 
    create_backend_transaction, remove_backend_transaction, can_write, save,
    close, and setattr.

    update_trans_flush_check_and_close, remove_trans_flush_check_and_close,
    and verify_trans_and_close are implemented entirly in terms of
    mark_transaction_dirty, mark_transaction_for_removal,
    mark_transaction_for_verification, flush_backend, transaction_is_clean,
    and close, functions you have to implement anyway, so that alone makes
    inheriting worthwhile.

    All backend modules should subclass persistent.Persistent (from zopedb),
    and dilegenly set self._p_changed where appropriate. 

    Bo-Keep backend modules are not expected to be thread-safe.

    A Bo-Keep backend module translates a Bo-Keep transaction (frontend) into
    some other form of data storage, a backend. This raises many of the
    clasical syncrhonization problems of trying to keep data in two places --
    there are potential issues such as changes being made directly to the
    backend system elsewhere, the backend being temporarilly unavailable,
    and the possibility of Bo-Keep making changes in the backend and
    not having the opportunity to record they were made. 

    Bo-Keep's approach to these complexities is to generally assume that
    an already successfuly created backend transaction hasn't been alterered.
    A backend transaction is considered to be "in-sync" with respect to the
    front end ("clean") unless bo-keep has been told that it might be
    "out of sync" with the front end or "dirty".

    If bo-keep is informed that a particular transaction is out of date,
    is is considered "dirty" until the backend has been syncrhonized with the
    front end again. If bo-keep is informed that a particular transaction no
    longer exists, this also makes it dirty. Bo-Keep may also request
    that a particular transaction be checked for consistency with the backend,
    until this check is completed the dirty status remains.

    to sumarize --
    clean means it is believed the front and back ends are in sync
    (but not activly verified)

    dirty means it is believed the front and back ends are possibly
    out of sync                      

    The bo-keep transaction (front end) should always be considered the
    authoritative data source. You should never intentionally alter backend
    data directly. Think of Bo-Keep as the master data source, and the backend
    as the slave data source. Where possible, you should take advantage of
    features in the underlying backend storage system that allow you to
    prevent changes to bo-keep backend transactions by sources other than
    bo-keep; or at least "mark" that data as belonging to bo-keep an make
    application logic in other systems respect that.

    That being said, backends do have a tendency to get modified by people
    not following the rules (or lax enformement of them),
    which is why requests for a consistency check can be made. In addition,
    if a backend transaction is being removed or replaced, a consistency check
    is automatically performed. If an inconsistency is found, bo-keep will
    not remove the underlying backend transaction. Manual intervention is
    required at that point to determine which side wins out.

    Another consideration in the Bo-keep backend design is the fact that
    some backends can be pretty slow when they read/write data out. This is
    why Bo-keep requires backend callers to first mark all the transactions
    that need to be changed or verified, and then call flush_backend()
    so that they are all possibly handled at the same time.

    update_trans_flush_check_and_close, remove_trans_flush_check_and_close,
    and verify_trans_and_close are convience functions that allow you to combine
    a request for change, flush_backend(), and close() together.

    You should expect close to be called anytime. Also, the other functions
    should still operate after a call to close, they are expected to
    re-aquire any resources required. close should be the last backend module
    function to be called.
    """

    @ends_with_commit
    def mark_transaction_dirty(self, trans_id, transaction):
        """Indicate a bo-keep transaction is not up to date in the backend.

        This doesn't trigger the backend update itself to occure, that only
        happens when flush_backend is called
 
        trans_id -- Bo-keep identifier for the transaction
        transaction -- The actual bo-keep transaction
        """
        pass

    def mark_transaction_for_verification(self, trans_id):
        """Indicate a bo-keep transaction should be compared against the backend

        This exists because there's always the chance of the backend being
        changed by evil forces, so a system administrator might want to
        check if bo-keep's database is out of sync with the backend

        Marking the transaction for verification doesn't cause it to happen
        right away, the verification is only done during the call to
        flush_backend . After that has taken place, you can check if the
        transaction is now considered dirty or not by calling
        transaction_is_clean . If you find it isn't clean, you can call
        reason_transaction_is_dirty to find out why.
        """
        pass

    @ends_with_commit
    def mark_transaction_for_hold(self, trans_id):
        pass

    @ends_with_commit
    def mark_transaction_for_removal(self, trans_id):
        pass

    @ends_with_commit
    def mark_transaction_for_forced_remove(self, trans_id):
        """Will ensure a transaction in a held state is removed despite
        being out of sync. If you want to try recreating the transaction
        again after, you have to flush_backend() after this, and then call
        mark_transaction_as_dirty and flush_backend()
        """
        pass

    def transaction_is_clean(self, trans_id):
        """Returns True if a transaction is not dirty, marked for removal,
        or in any other state than the normal one
        """
        return True

    def reason_transaction_is_dirty(self, trans_id):
        """Returns a string that describes why a particular transaction is still
        dirty, marked for removal, or in any other non-clean / non-normal state.

        You should only call this if you've first called transaction_is_clean(),
        otherwise it isn't meaningful and will give you an exception

        You will get an error if you call this when trans_id doesn't
        exist
        """
        raise BoKeepBackendException("the transaction isn't dirty")

    def flush_backend(self):
        """Take all transactions that are dirty or marked for removal
        writes them out / removes them out if possible.

        When this is done, it does a zopedb transaction commit, if you're
        sharing a zopedb thread with this you'll want to be sure your data
        is in a state you're comfortable having commited
        """
        pass

    def close(self, close_reason='reset because close() was called'):
        """Instructs the module to release any resources being used to
        access the backend.

        This should be called when done with a backend module.

        Any other calls made since the last call to flush_backend may be lost()
        """
        pass

    def configure_backend(self, parent_window=None):
        """Instructs the plugin to create a configuration dialog
        provide the parent window or None
        """
        pass

    def backend_account_dialog(self, parent_window=None):
        return None, ''
    
    @ends_with_commit
    def update_trans_flush_check_and_close(self, trans_id, transaction):
        """When this is done, it does a zopedb transaction commit, if you're
        sharing a zopedb thread with this you'll want to be sure your data
        is in a state you're comfortable having commited
        """
        self.mark_transaction_dirty(trans_id, transaction)
        self.flush_backend()
        is_clean = self.transaction_is_clean(trans_id)
        self.close()
        return is_clean
    
    @ends_with_commit
    def remove_trans_flush_check_and_close(self, trans_id):
        """When this is done, it does a zopedb transaction commit, if you're
        sharing a zopedb thread with this you'll want to be sure your data
        is in a state you're comfortable having commited
        """
        self.mark_transaction_for_removal(trans_id)
        self.flush_backend()
        is_gone = trans_id not in self.dirty_transaction_set
        self.close()
        return is_gone

    @ends_with_commit
    def verify_trans_and_close(self, trans_id):
        """When this is done, it does a zopedb transaction commit, if you're
        sharing a zopedb thread with this you'll want to be sure your data
        is in a state you're comfortable having commited
        """
        self.mark_transaction_for_verification(trans_id)
        self.flush_backend()
        is_clean = self.transaction_is_clean(trans_id)
        self.close()
        return is_clean

    # TODO convience functions for hold and forced remove

    @ends_with_commit
    def setattr(self, attr, value):
        """When this is done, it does a zopedb transaction commit, if you're
        sharing a zopedb thread with this you'll want to be sure your data
        is in a state you're comfortable having commited
        """
        setattr(self, attr, value)
        self.flush_backend()

   

class BoKeepBackendException(Exception):
    pass

class BoKeepBackendResetException(Exception):
    """Subclasses of BackendModule can raise this to indicate that
    changes via create_backend_transaction() and remove_backend_changes()
    made since the last successful save have been lost.

    A BackendModule should raise this immediatly when it becomes true, and not
    write new changes (that aren't lost) to the backend prior to raising this.
    """
    pass

