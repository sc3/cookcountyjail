
import gevent
from mock import Mock, call

from countyapi.management.scraper.inmates import Inmates


class TestInmates:

    def test_add_inmate(self):
        Inmate_TestDouble.clear_class_vars()
        inmates = Inmates(Inmate_TestDouble, Mock())
        inmates.add(self)
        gevent.sleep(0)
        assert Inmate_TestDouble.instantiated_called(1)
        inmate = Inmate_TestDouble.instantiated[0]
        assert inmate.inmate_details == self
        assert inmate.saved_count == 1

    def test_finish(self):
        Inmate_TestDouble.clear_class_vars()
        monitor = Mock()
        inmates = Inmates(Inmate_TestDouble, monitor)
        inmates.finish()
        gevent.sleep(0)
        assert monitor.notify.call_args_list == [call(inmates.__class__, Inmates.FINISHED_PROCESSING)]


class Inmate_TestDouble:

    instantiated = []

    def __init__(self, inmate_details, monitor):
        Inmate_TestDouble.instantiated.append(self)
        self.inmate_details = inmate_details
        self._monitor = monitor
        self.saved_count = 0

    @staticmethod
    def clear_class_vars():
        Inmate_TestDouble.instantiated = []

    @staticmethod
    def instantiated_called(expected_call_count):
        return len(Inmate_TestDouble.instantiated) == expected_call_count

    def save(self):
        self.saved_count += 1
