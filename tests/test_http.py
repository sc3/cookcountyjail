
import gevent
import grequests
import requests
from random import random

BAD_URL_NETWORK_PROBLEM = 'Bad url or network problem.'

COOK_COUNTY_JAIL_INMATE_DETAILS_URL = \
    'http://www2.cookcountysheriff.org/search2/details.asp?jailnumber='


class Http:

    _STD_INITIAL_SLEEP_PERIOD = 0.1
    _STD_NUMBER_ATTEMPTS = 3
    _STD_SLEEP_PERIODS = [1.61, 7, 13, 23, 41]

    def __init__(self):
        pass

    def get(self, url, number_attempts=_STD_NUMBER_ATTEMPTS, initial_sleep_period=_STD_INITIAL_SLEEP_PERIOD):
        attempt = 1
        sleep_period = initial_sleep_period
        while attempt <= number_attempts:
            gevent.sleep(sleep_period)
            try:
                request = grequests.get(url)
                grequests.map([request])
                if request.response is not None:
                    if request.response.status_code == requests.codes.ok:
                        return True, request.response.text
                else:
                    return False, BAD_URL_NETWORK_PROBLEM
            except requests.exceptions.RequestException:
                return False, BAD_URL_NETWORK_PROBLEM
            sleep_period = self._get_next_sleep_period(sleep_period, attempt)
            attempt += 1
        return False, {'status-code': request.response.status_code}

    def _get_next_sleep_period(self, current_sleep_period, attempt):
        """
        get_next_sleep_period - implements a cascading fall off sleep period with
        a bit of randomness control the periods by setting the values in the
        array, STD_SLEEP_PERIODS
        """
        index = attempt - 1
        if index >= len(self._STD_SLEEP_PERIODS):
            index = -1
        return current_sleep_period * random() + self._STD_SLEEP_PERIODS[index]


import httpretty
from random import randint


class Test_Http:

    @httpretty.activate
    def test_get_succeeds(self):
        number_of_attempts = 2
        expected_text = 'it worked'
        inmate_url = COOK_COUNTY_JAIL_INMATE_DETAILS_URL + '2014-0118034'
        ccj_api_requests = {'succeed-attempt': randint(1, number_of_attempts), 'current-attempt': 0}

        def fulfill_ccj_api_request(_, uri, headers):
            assert uri == inmate_url
            ccj_api_requests['current-attempt'] += 1
            if ccj_api_requests['current-attempt'] == ccj_api_requests['succeed-attempt']:
                return 200, headers, expected_text
            return 500, headers, 'did not work'

        httpretty.register_uri(httpretty.GET, COOK_COUNTY_JAIL_INMATE_DETAILS_URL,
                               body=fulfill_ccj_api_request)

        http = Http()
        okay, fetched_contents = http.get(inmate_url, number_of_attempts)

        assert okay
        assert ccj_api_requests['current-attempt'] == ccj_api_requests['succeed-attempt']
        assert fetched_contents == expected_text

    @httpretty.activate
    def test_get_fails_500(self):
        number_of_attempts = 2
        expected_text = 'did not work'
        inmate_url = COOK_COUNTY_JAIL_INMATE_DETAILS_URL + '2014-0118034'
        ccj_api_requests = {'succeed-attempt': number_of_attempts, 'current-attempt': 0}

        def fulfill_ccj_api_request(_, uri, headers):
            assert uri == inmate_url
            ccj_api_requests['current-attempt'] += 1
            return 500, headers, expected_text

        httpretty.register_uri(httpretty.GET, COOK_COUNTY_JAIL_INMATE_DETAILS_URL,
                               body=fulfill_ccj_api_request)

        http = Http()
        okay, fetched_contents = http.get(inmate_url, number_of_attempts)

        assert not okay
        assert ccj_api_requests['current-attempt'] == ccj_api_requests['succeed-attempt']
        assert fetched_contents['status-code'] == 500

    def test_get_fails_no_such_place(self):
        inmate_url = 'http://idbvf3ruvfr3ubububufvubeuvdvd2uvuevvgud2bewhde.duucuvcryvgrfvyv'
        http = Http()
        okay, fetched_contents = http.get(inmate_url)

        assert not okay
        assert fetched_contents == BAD_URL_NETWORK_PROBLEM
