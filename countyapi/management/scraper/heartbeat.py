
import gevent

ONE_SECOND = 1


class Heartbeat:
    """
    Generate a 'Heartbeat' notification every second
    """

    def __init__(self, monitor):
        self._monitor = monitor
        gevent.spawn(self._heartbeat)

    def _heartbeat(self):
        while True:
            gevent.sleep(ONE_SECOND)
            self._monitor.notify(self.__class__)
