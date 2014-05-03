from datetime import date

from utils import ONE_DAY, yesterday
from concurrent_base import ConcurrentBase


class Inmates(ConcurrentBase):

    def __init__(self, inmate_class, monitor):
        super(Inmates, self).__init__(monitor)
        self._inmate_class = inmate_class

    def active_inmates_ids(self, response_queue):
        self._put(self._active_inmates_ids, response_queue)

    def _active_inmates_ids(self, response_queue):
        _send_inmate_ids(response_queue, self._inmate_class.active_inmates())

    def add(self, inmate_id, inmate_details):
        self._put(self._create_update_inmate, {'inmate_id': inmate_id, 'inmate_details': inmate_details})

    def _create_update_inmate(self, args):
        inmate = self._inmate_class(args['inmate_id'], args['inmate_details'], self._monitor)
        inmate.save()

    def discharge(self, inmate_id):
        self._put(self._discharge, inmate_id)

    def _discharge(self, inmate_id):
        self._inmate_class.discharge(inmate_id, self._monitor)

    def known_inmates_ids_starting_with(self, response_queue, start_date):
        self._put(self._known_inmates_ids_starting_with, {'response_queue': response_queue, 'start_date': start_date})

    def _known_inmates_ids_starting_with(self, args):
        known_inmates_ids = []
        cur_date = args['start_date']
        yesterday = _yesterday()
        while cur_date <= yesterday:
            known_inmates_ids.extend([inmate.jail_id for inmate in self._inmate_class.known_inmates_for_date(cur_date)])
            cur_date += ONE_DAY
        args['response_queue'].put(known_inmates_ids)

    def recently_discharged_inmates_ids(self, response_queue):
        self._put(self._recently_discharged_inmates_ids, response_queue)

    def _recently_discharged_inmates_ids(self, response_queue):
        _send_inmate_ids(response_queue, self._inmate_class.recently_discharged_inmates())

    def update(self, inmate_id, inmate_details):
        self._put(self._create_update_inmate, {'inmate_id': inmate_id, 'inmate_details': inmate_details})


def _send_inmate_ids(response_queue, inmates):
    inmates_ids = [inmate.jail_id for inmate in inmates]
    response_queue.put(inmates_ids)

