

from datetime import datetime
from countyapi.management.scraper.monitor import Monitor
from countyapi.management.scraper.heartbeat import Heartbeat


class TestHeartbeat:

    def test_that_it_generates_heartbeats(self):
        monitor = Monitor(None)
        heartbeat = Heartbeat(monitor)
        number_heartbeats_to_collect = 5
        heartbeats = [monitor.notification() for _ in range(number_heartbeats_to_collect)]
        assert len(heartbeats) == number_heartbeats_to_collect
        for hb in heartbeats:
            assert isinstance(hb[0], datetime)
            assert hb[1] == heartbeat.__class__
        for i in range(number_heartbeats_to_collect - 1):
            x = heartbeats[i + 1][0] - heartbeats[i][0]
            assert x.seconds == 1
