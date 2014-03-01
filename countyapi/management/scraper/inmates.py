
import gevent
from gevent.queue import JoinableQueue
from datetime import date, timedelta

ONE_DAY = timedelta(1)

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
        _send_inmate_ids(response_queue, self._inmate_class.active_inmates())

    def add(self, inmate_details):
        self._put(self._create_update_inmate, inmate_details)

    def _create_update_inmate(self, inmate_details):
        inmate = self._inmate_class(inmate_details, self._monitor)
        inmate.save()

    def _debug(self, msg):
        self._monitor.debug('Inmates: %s' % msg)

    def discharge(self, inmate_id):
        self._put(self._discharge, inmate_id)

    def _discharge(self, inmate_id):
        self._inmate_class.discharge(inmate_id, self._monitor)

    def finish(self):
        self._prevent_new_requests_from_being_processed()
        gevent.spawn(self._wait_for_processing_to_finish)
        gevent.sleep(0)

    def known_inmates_ids_starting_with(self, response_queue, start_date):
        self._put(self._known_inmates_ids_starting_with, {'response_queue': response_queue, 'start_date': start_date})

    def _known_inmates_ids_starting_with(self, args):
        known_inmates_ids = []
        cur_date = args['start_date']
        yesterday = _yesterday()
        while cur_date <= yesterday:
            known_inmates_ids.extend([inmate.jail_id for inmate in self._inmate_class.known_inmates_for_date(cur_date)])
            cur_date += ONE_DAY
        args['response_queue'].put(known_inmates_ids)

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

    def recently_discharged_inmates_ids(self, response_queue):
        self._put(self._recently_discharged_inmates_ids, response_queue)

    def _recently_discharged_inmates_ids(self, response_queue):
        _send_inmate_ids(response_queue, self._inmate_class.recently_discharged_inmates())

    def _setup_command_system(self):
        return JoinableQueue(None), [gevent.spawn(self._process_commands)]

    def update(self, inmate_details):
        self._put(self._create_update_inmate, inmate_details)

    def _wait_for_processing_to_finish(self):
        self._read_commands_q.join()
        self._monitor.notify(self.__class__, self.FINISHED_PROCESSING)


def _send_inmate_ids(response_queue, inmates):
    inmates_ids = [inmate.jail_id for inmate in inmates]
    response_queue.put(inmates_ids)


def _yesterday():
    return date.today() - ONE_DAY
