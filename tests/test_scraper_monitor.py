
from countyapi.management.scraper.monitor import Monitor

from mock import Mock


class Test_MonitorDebugLogging:

    def test_debug_msg(self):
        expected = 'hi'
        log = Mock()
        monitor = Monitor(log)
        monitor.debug(expected)
        log.debug.assert_called_once_with(expected)

    def test_debug_msg_not_output_debug_off(self):
        expected = 'hi'
        log = Mock()
        monitor = Monitor(log, no_debug_msgs=True)
        monitor.debug(expected)
        assert not log.debug.called, 'log.debug should not have been called'
