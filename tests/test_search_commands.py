
from mock import Mock, call
from datetime import date, timedelta

ONE_DAY = timedelta(1)

from countyapi.management.scraper.search_commands import SearchCommands


class Test_SearchCommands:

    def test_find_inmates(self):
        number_to_fetch = 3
        expected = expect_jail_id_calls(number_to_fetch)
        inmate_scraper = Mock()
        search_commands = SearchCommands(inmate_scraper)
        search_commands.find_inmates(number_to_fetch=number_to_fetch)
        assert inmate_scraper.create_if.call_args_list == expected

    def test_find_inmates_with_exclude_list(self):
        number_to_fetch = 4
        expected = expect_jail_id_calls(number_to_fetch)
        inmate_scraper = Mock()
        search_commands = SearchCommands(inmate_scraper)
        search_commands.find_inmates(gen_inmate_ids(number_to_fetch)[1:-1], number_to_fetch=number_to_fetch)
        assert inmate_scraper.create_if.call_args_list == [expected[0], expected[number_to_fetch - 1]]


def expect_jail_id_calls(number_to_fetch):
    expected = []
    for jail_id in gen_inmate_ids(number_to_fetch):
        expected.append(call(jail_id))
    return expected


def gen_inmate_ids(num_to_gen):
    booking_date = date.today() - ONE_DAY
    prefix = booking_date.strftime("%Y-%m%d") + '%03d'
    return [prefix % num for num in range(1, num_to_gen + 1)]
