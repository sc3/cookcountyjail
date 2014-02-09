
from countyapi.management.scraper.monitor import Monitor

from mock import Mock, patch
from datetime import datetime


class Test_Monitor:

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

    def test_notify(self):
        timestamp = datetime.now()
        with patch("countyapi.management.scraper.monitor.datetime") as mock_datetime:
            mock_datetime.now.return_value = timestamp
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            notifier = Mock(spec=Test_Monitor)
            expected = (timestamp, notifier, '')
            monitor = Monitor(None)
            monitor.notify(notifier)
            assert monitor.notification() == expected
