
import gevent
from gevent.queue import JoinableQueue

from throwable_commands_queue import ThrowawayCommandsQueue


class Inmates:

    FINISHED_PROCESSING = 'Inmates_finished_processing'

    def __init__(self, inmate_class, monitor):
        self._inmate_class = inmate_class
        self._monitor = monitor
        self._read_commands_q, self._workers = self._setup_command_system()
        self._write_commands_q = self._read_commands_q
        gevent.sleep(0)

    def active_inmates_ids(self, response_queue):
        self._put(self._active_inmates_ids, response_queue)

    def _active_inmates_ids(self, response_queue):
        self._debug('started fetching active inmates ids')
        inmates_ids = [inmate.jail_id for inmate in self._inmate_class.active_inmates()]
        response_queue.put(inmates_ids)
        self._debug('finished fetching active inmates ids')

    def add(self, inmate_details):
        self._put(self._create_update_inmate, inmate_details)

    def _create_update_inmate(self, inmate_details):
        msg_template = '%%s create_update_inmate - %s' % inmate_details.jail_id()
        self._debug(msg_template % 'started')
        inmate = self._inmate_class(inmate_details, self._monitor)
        inmate.save()
        self._debug(msg_template % 'finished')

    def _debug(self, msg):
        self._monitor.debug('Inmates: %s' % msg)

    def discharge(self, inmate_id):
        self._put(self._discharge, inmate_id)

    def _discharge(self, inmate_id):
        debug_msg_template = '%%s discharge inmate %s' % inmate_id
        self._debug(debug_msg_template % 'started')
        self._inmate_class.discharge(inmate_id, self._monitor)
        self._debug(debug_msg_template % 'finished')

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

    def _put(self, method, args):
        self._write_commands_q.put((method, args))
        gevent.sleep(0)

    def _setup_command_system(self):
        return JoinableQueue(None), [gevent.spawn(self._process_commands)]

    def update(self, inmate_details):
        self._put(self._create_update_inmate, inmate_details)

    def _wait_for_processing_to_finish(self):
        self._debug('started waiting for inmates processing to finish')
        self._read_commands_q.join()
        self._monitor.notify(self.__class__, self.FINISHED_PROCESSING)
        self._debug('finished waiting for inmates processing to finish')
