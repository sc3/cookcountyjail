
from heartbeat import Heartbeat


class Controller:

    STOP_COMMAND = '*_Halt_*'

    def __init__(self, log, monitor):
        self._log = log
        self.heartbeat_count = 0
        self.is_running = False
        self._keep_running = True
        self._monitor = monitor
        self._heartbeat = None
        self._heartbeat_class = None

    def run(self):
        self._heartbeat = Heartbeat(self._monitor)
        self._heartbeat_class = self._heartbeat.__class__
        self.is_running = True
        keep_running = True
        while keep_running:
            timestamp, notifier, msg = self._monitor.notification()
            if notifier == self._heartbeat_class:
                self.heartbeat_count += 1
            elif msg == self.STOP_COMMAND:
                keep_running = False
        self.is_running = False

    def stop_command(self):
        return self.STOP_COMMAND
