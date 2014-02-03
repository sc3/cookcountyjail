
import gevent
from gevent.queue import JoinableQueue

from inmate import Inmate

from throwable_commands_queue import ThrowawayCommandsQueue


class Inmates:

    def __init__(self):
        self._read_commands_q = self._setup_command_system()
        self._write_commands_q = self._read_commands_q

    def add(self, inmate_details):
        self._write_commands_q.put((_create_update_inmate, inmate_details))
        gevent.sleep(0)

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
        commands = JoinableQueue(0)
        gevent.spawn(self._process_commands)
        return commands

    def _wait_for_processing_to_finish(self):
        self._read_commands_q.join()


def _create_update_inmate(inmate_details):
    inmate = Inmate(inmate_details)
    inmate.save()
