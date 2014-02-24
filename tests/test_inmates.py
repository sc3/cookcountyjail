
import gevent
from mock import Mock, call

from countyapi.management.scraper.inmates import Inmates


class TestInmates:

    def test_add_inmate(self):
        Inmate_TestDouble.clear_class_vars()
        inmates = Inmates(Inmate_TestDouble, Mock())
        inmate_details = Mock()
        inmate_details.jail_id.return_value = 23
        inmates.add(inmate_details)
        assert Inmate_TestDouble.instantiated_called(1)
        inmate = Inmate_TestDouble.instantiated[0]
        assert inmate.inmate_details == inmate_details
        assert inmate.saved_count == 1

    def test_update_inmate(self):
        Inmate_TestDouble.clear_class_vars()
        inmates = Inmates(Inmate_TestDouble, Mock())
        inmate_details = Mock()
        inmate_details.jail_id.return_value = 23
        inmates.update(inmate_details)
        assert Inmate_TestDouble.instantiated_called(1)
        inmate = Inmate_TestDouble.instantiated[0]
        assert inmate.inmate_details == inmate_details
        assert inmate.saved_count == 1

    def test_discharge_inmate(self):
        inmate_class = Mock()
        monitor = Mock()
        inmates = Inmates(inmate_class, monitor)
        inmate__id = 232
        inmates.discharge(inmate__id)
        assert inmate_class.discharge.call_args_list == [call(inmate__id, monitor)]

    def test_finish(self):
        Inmate_TestDouble.clear_class_vars()
        monitor = Mock()
        inmates = Inmates(Inmate_TestDouble, monitor)
        inmates.finish()
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
        instantiated = Inmate_TestDouble.instantiated
        return len(instantiated) == expected_call_count

    def save(self):
        self.saved_count += 1
