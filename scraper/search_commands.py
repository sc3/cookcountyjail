from datetime import date

from utils import ONE_DAY, yesterday
from concurrent_base import ConcurrentBase

MAX_INMATE_NUMBER = 350


class SearchCommands(ConcurrentBase):

    _NOTIFICATION_MSG_TEMPLATE = 'SearchCommands: finished generating %s'
    FINISHED_FIND_INMATES = _NOTIFICATION_MSG_TEMPLATE % 'find inmates commands'
    FINISHED_CHECK_OF_RECENTLY_DISCHARGED_INMATES = \
        _NOTIFICATION_MSG_TEMPLATE % 'check of recently discharged inmates commands'
    FINISHED_UPDATE_INMATES_STATUS = _NOTIFICATION_MSG_TEMPLATE % 'update inmates status'

    def __init__(self, inmate_scraper, monitor):
        super(SearchCommands, self).__init__(monitor)
        self._inmate_scraper = inmate_scraper

    def check_if_really_discharged(self, discharged_inmates_ids):
        self._put(self._check_if_really_discharged, discharged_inmates_ids)

    def _check_if_really_discharged(self, discharged_inmates_ids):
        for discharged_inmate_id in discharged_inmates_ids:
            self._inmate_scraper.resurrect_if_found(discharged_inmate_id)
        self._notify(self.FINISHED_CHECK_OF_RECENTLY_DISCHARGED_INMATES)

    def find_inmates(self, exclude_list=None, number_to_fetch=MAX_INMATE_NUMBER, start_date=None):
        if exclude_list is None:
            exclude_list = []
        if start_date is None:
            start_date = yesterday()
        self._put(self._find_inmates, {'excluded_inmates': exclude_list, 'number_to_fetch': number_to_fetch,
                                       'start_date': start_date})

    def _find_inmates(self, args):
        excluded_inmates = set(args['excluded_inmates'])
        cur_date = args['start_date']
        while cur_date <= yesterday():
            for inmate_id in _jail_ids(cur_date, args['number_to_fetch']):
                if inmate_id not in excluded_inmates:
                    self._inmate_scraper.create_if_exists(inmate_id)
            cur_date += ONE_DAY
        self._notify(self.FINISHED_FIND_INMATES)

    def update_inmates_status(self, active_inmates_ids):
        self._put(self._update_inmates_status, active_inmates_ids)

    def _update_inmates_status(self, active_inmates_ids):
        for inmate_id in active_inmates_ids:
            self._inmate_scraper.update_inmate_status(inmate_id)
        self._notify(self.FINISHED_UPDATE_INMATES_STATUS)


def _jail_ids(cur_date, number_to_fetch):
    prefix = cur_date.strftime("%Y-%m%d") + '%03d'
    for booking_number in range(1, number_to_fetch + 1):
        yield prefix % booking_number

