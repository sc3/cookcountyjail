

from datetime import datetime
from countyapi.management.scraper.monitor import Monitor
from countyapi.management.scraper.heartbeat import Heartbeat


class TestHeartbeat:

    def test_that_it_generates_heartbeats(self):
        monitor = Monitor(None)
        heartbeat = Heartbeat(monitor)
        number_heartbeats_to_collect = 2
        starting_time = datetime.now()
        heartbeats = [monitor.notification() for _ in range(number_heartbeats_to_collect)]
        ending_time = datetime.now()
        assert len(heartbeats) == number_heartbeats_to_collect
        assert (ending_time - starting_time).seconds == number_heartbeats_to_collect
        for hb in heartbeats:
            assert hb[0] == heartbeat.__class__
