
from scraper.monitor import Monitor, MONITOR_VERBOSE_DMSG_LEVEL

from mock import Mock, call


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

    def test_verbose_debug_mode(self):
        expected = 'hi'
        log = Mock()
        monitor = Monitor(log)
        monitor.debug(expected)
        monitor.debug(expected, debug_level=MONITOR_VERBOSE_DMSG_LEVEL)
        assert len(log.debug.call_args_list) == 1
        log = Mock()
        monitor = Monitor(log, verbose_debug_mode=True)
        monitor.debug(expected)
        monitor.debug(expected, debug_level=MONITOR_VERBOSE_DMSG_LEVEL)
        assert len(log.debug.call_args_list) == 2

    def test_notify(self):
        notifier = Mock(spec=Test_Monitor)
        expected = (notifier, '')
        monitor = Monitor(None)
        monitor.notify(notifier)
        assert monitor.notification() == expected
