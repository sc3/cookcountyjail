
from datetime import date, timedelta

import gevent
from gevent.queue import Queue


MAX_INMATE_NUMBER = 350

ONE_DAY = timedelta(1)


class SearchCommands:

    def __init__(self, inmate_scraper):
        self._inmate_scraper = inmate_scraper
        self._commands = self._setup_command_system()

    def find_inmates(self, exclude_list=None, number_to_fetch=MAX_INMATE_NUMBER):
        if exclude_list is None:
            exclude_list = []
        self._commands.put((self._find_inmates, {'excluded_inmates': exclude_list,
                                                 'number_to_fetch': number_to_fetch}))
        gevent.sleep(0)

    def _find_inmates(self, args):
        excluded_inmates = set(args['excluded_inmates'])
        for inmate_id in self._jail_ids(args['number_to_fetch']):
            if inmate_id not in excluded_inmates:
                self._inmate_scraper.create_if_exists(inmate_id)

    def _jail_ids(self, number_to_fetch):
        booking_date = date.today() - ONE_DAY
        prefix = booking_date.strftime("%Y-%m%d") + '%03d'
        for booking_number in range(1, number_to_fetch + 1):
            yield prefix % booking_number  # add to the prefix the current booking number

    def _process_commands(self):
        while True:
            func, args = self._commands.get()
            func(args)

    def _setup_command_system(self):
        commands = Queue(0)
        gevent.spawn(self._process_commands)
        return commands
