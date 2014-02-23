
import gevent
from gevent.queue import JoinableQueue

from throwable_commands_queue import ThrowawayCommandsQueue


class Inmates:

    FINISHED_PROCESSING = 'Inmates_finished_processing'

    def __init__(self, inmate_class, monitor):
        self.inmate_class = inmate_class
        self._monitor = monitor
        self._read_commands_q, self._workers = self._setup_command_system()
        self._write_commands_q = self._read_commands_q
        gevent.sleep(0)

    def add(self, inmate_details):
        self._write_commands_q.put((self._create_update_inmate, inmate_details))
        gevent.sleep(0)

    def _create_update_inmate(self, inmate_details):
        self._debug('started create_update_inmate')
        inmate = self.inmate_class(inmate_details, self._monitor)
        inmate.save()
        self._debug('finished create_update_inmate')

    def _debug(self, msg):
        self._monitor.debug('Inmates: %s' % msg)

    def finish(self):
        self._prevent_new_requests_from_being_processed()
        gevent.spawn(self._wait_for_processing_to_finish)
        gevent.sleep(0)

    def _prevent_new_requests_from_being_processed(self):
        self._write_commands_q = ThrowawayCommandsQueue()

    def _process_commands(self):
        while True:
            try:
                func, args = self._read_commands_q.get()
                func(args)
            finally:
                self._read_commands_q.task_done()

    def _setup_command_system(self):
        return JoinableQueue(0), [gevent.spawn(self._process_commands)]

    def _wait_for_processing_to_finish(self):
        self._debug('started waiting for inmates processing to finish')
        self._read_commands_q.join()
        self._monitor.notify(self.__class__, self.FINISHED_PROCESSING)
        self._debug('finished waiting for inmates processing to finish')
