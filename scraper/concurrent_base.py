from datetime import date

import gevent
from gevent.queue import JoinableQueue
from monitor import MONITOR_VERBOSE_DMSG_LEVEL
from throwable_commands_queue import ThrowawayCommandsQueue


class ConcurrentBase(object):


    """
    Provides the following useful methods to its inheriting classes:

    + _debug()
    + _notify()
    + _put()
    + finish()

    """
    
    def __init__(self, monitor, workers=1):
        self.klass = type(self)
        self.klass_name = self.klass.__name__
        self.FINISHED_PROCESSING = '{0}: finished processing'.format(self.klass_name)
        self._monitor = monitor
        self._workers_to_start = workers
        self._setup_command_system()
        gevent.sleep(0)

    def _debug(self, msg, debug_level=None):
        self._monitor.debug('{0}: {1}'.format(self.klass_name, msg), debug_level)

    def finish(self):
        self._prevent_new_requests_from_being_processed()
        gevent.spawn(self._wait_for_processing_to_finish)
        gevent.sleep(0)

    def _notify(self, notification_msg):
        self._monitor.notify(self.klass, notification_msg)

    def _prevent_new_requests_from_being_processed(self):
        # don't accept new commands after receiving a finish command
        self._write_commands_q = ThrowawayCommandsQueue()
    
    def _process_commands(self):
        while True:
            try:
                ## do arbitrary command
                func, args = self._read_commands_q.get()
                func(args)
            finally:
                self._read_commands_q.task_done()

    def _put(self, method, args):
        ## tell some worker to do arbitrary command
        self._write_commands_q.put((method, args))
        gevent.sleep(0)


    def _setup_command_system(self):
        # we have two refs to the commands queue,
        # but write_commands_q will switch to throwaway
        # after we receive a finish command
        self._read_commands_q = JoinableQueue(None)
        self._write_commands_q = self._read_commands_q 
        for x in range(self._workers_to_start):
            gevent.spawn(self._process_commands)

    def _wait_for_processing_to_finish(self):
        self._read_commands_q.join()
        self._monitor.notify(self.klass, self.FINISHED_PROCESSING)

        