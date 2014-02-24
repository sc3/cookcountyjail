
from countyapi.management.scraper.monitor import Monitor

from mock import Mock


class Test_Monitor:

    def test_debug_msg(self):
        timestamp = '*now*'
        msg = 'hi'
        expected = '%s - %s' % (str(timestamp), msg)
        log = Mock()
        monitor = Monitor(log)
        monitor._debug(timestamp, msg)
        log.debug.assert_called_once_with(expected)

    def test_debug_msgs_off(self):
        expected = 'hi'
        log = Mock()
        monitor = Monitor(log, no_debug_msgs=True)
        monitor.debug(expected)
        assert not log.debug.called, 'log.debug should not have been called'

    def test_notify(self):
        notifier = Mock(spec=Test_Monitor)
        expected = (notifier, '')
        monitor = Monitor(None)
        monitor.notify(notifier)
        assert monitor.notification() == expected
