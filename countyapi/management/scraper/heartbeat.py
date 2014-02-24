
import gevent

HEARTBEAT_INTERVAL = 1


class Heartbeat:
    """
    Generate a 'Heartbeat' notification every second
    """

    def __init__(self, monitor):
        self._monitor = monitor
        gevent.spawn(self._heartbeat)

    def _heartbeat(self):
        while True:
            gevent.sleep(HEARTBEAT_INTERVAL)
            self._monitor.notify(self.__class__)
