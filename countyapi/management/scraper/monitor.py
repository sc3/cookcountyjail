
import gevent
from gevent.queue import Queue


class Monitor:
    def __init__(self, log, no_debug_msgs=False):
        self._log = log
        self._debug_msgs = not no_debug_msgs
        self._messages = self._setup_msg_system()

    def debug(self, msg):
        if self._debug_msgs:
            self._messages.put(msg)
            gevent.sleep(0)

    def _process_msgs(self):
        while True:
            msg = self._messages.get()
            self._log.debug(msg)

    def _setup_msg_system(self):
        messages = Queue(0)
        gevent.spawn(self._process_msgs)
        return messages
