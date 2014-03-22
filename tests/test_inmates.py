
from gevent.queue import Queue
from mock import Mock, call

from countyapi.management.scraper.inmates import Inmates


class TestInmates:

    def test_active_inmates_ids(self):
        inmate_class = Mock()
        j_ids = [j_id for j_id in range(1, 4)]
        input_values = [make_county_inmate(j_id) for j_id in j_ids]
        inmate_class.active_inmates.return_value = input_values
        inmates = Inmates(inmate_class, Mock())
        response_q = Queue(1)
        inmates.active_inmates_ids(response_q)
        active_inmates_ids = response_q.get()
        assert active_inmates_ids == j_ids

    def test_add_inmate(self):
        Inmate_TestDouble.clear_class_vars()
        inmates = Inmates(Inmate_TestDouble, Mock())
        inmate_details = Mock()
        inmate_id = 23
        inmate_details.jail_id.return_value = inmate_id
        inmates.add(inmate_id, inmate_details)
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

    def test_recently_discharged_inmates_ids(self):
        inmate_class = Mock()
        j_ids = [j_id for j_id in range(1, 4)]
        input_values = [make_county_inmate(j_id) for j_id in j_ids]
        inmate_class.recently_discharged_inmates.return_value = input_values
        inmates = Inmates(inmate_class, Mock())
        response_q = Queue(1)
        inmates.recently_discharged_inmates_ids(response_q)
        recently_discharged_inmates_ids = response_q.get()
        assert recently_discharged_inmates_ids == j_ids

    def test_update_inmate(self):
        Inmate_TestDouble.clear_class_vars()
        inmates = Inmates(Inmate_TestDouble, Mock())
        inmate_details = Mock()
        inmate_id = 23
        inmate_details.jail_id.return_value = inmate_id
        inmates.update(inmate_id, inmate_details)
        assert Inmate_TestDouble.instantiated_called(1)
        inmate = Inmate_TestDouble.instantiated[0]
        assert inmate.inmate_details == inmate_details
        assert inmate.saved_count == 1


class Inmate_TestDouble:

    instantiated = []

    def __init__(self, inmate_id, inmate_details, monitor):
        Inmate_TestDouble.instantiated.append(self)
        self.inmate_id = inmate_id
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


def make_county_inmate(inmate_id):
    county_inmate = Mock()
    county_inmate.jail_id = inmate_id
    return county_inmate
