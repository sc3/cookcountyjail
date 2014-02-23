
import gevent
from gevent.queue import Queue
from datetime import datetime


class Monitor:
    """
    Provides capabilities for monitoring operations:
        logging:
            debug
        notifications
    """

    def __init__(self, log, no_debug_msgs=False):
        self._log = log
        self._debug_msgs = not no_debug_msgs
        self._messages = self._setup_msg_system()
        self._notifications = self._setup_notification_queue()

    def debug(self, msg):
        if self._debug_msgs:
            self._debug(datetime.now(), msg)

    def _debug(self, timestamp, msg):
        self._messages.put((timestamp, msg))
        gevent.sleep(0)

    def notification(self):
        notification = self._notifications.get()
        return notification

    def notify(self, notifier, msg=''):
        self._notifications.put((notifier, msg))
        gevent.sleep(0)

    def _process_msgs(self):
        while True:
            msg = self._messages.get()
            self._log.debug('%s - %s' % msg)

    def _setup_msg_system(self):
        messages = Queue(0)
        gevent.spawn(self._process_msgs)
        return messages

    def _setup_notification_queue(self):
        return Queue(0)
