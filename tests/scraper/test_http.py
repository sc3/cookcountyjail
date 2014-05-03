

import httpretty
from random import randint

from scraper.http import Http, COOK_COUNTY_JAIL_INMATE_DETAILS_URL, BAD_URL_NETWORK_PROBLEM


INMATE_URL = COOK_COUNTY_JAIL_INMATE_DETAILS_URL + '2014-0118034'


class Test_Http:

    @httpretty.activate
    def test_get_succeeds(self):
        number_of_attempts = 2
        expected_text = 'it worked'
        ccj_api_requests = {'succeed-attempt': randint(1, number_of_attempts), 'current-attempt': 0}

        def fulfill_ccj_api_request(_, uri, headers):
            assert uri == INMATE_URL
            ccj_api_requests['current-attempt'] += 1
            if ccj_api_requests['current-attempt'] == ccj_api_requests['succeed-attempt']:
                return 200, headers, expected_text
            return 500, headers, 'did not work'

        httpretty.register_uri(httpretty.GET, COOK_COUNTY_JAIL_INMATE_DETAILS_URL,
                               body=fulfill_ccj_api_request)

        http = Http()
        okay, fetched_contents = http.get(INMATE_URL, number_of_attempts)

        assert okay
        assert ccj_api_requests['current-attempt'] == ccj_api_requests['succeed-attempt']
        assert fetched_contents == expected_text

    @httpretty.activate
    def test_get_fails_500(self):
        number_of_attempts = 2
        expected_text = 'did not work'
        ccj_api_requests = {'succeed-attempt': number_of_attempts, 'current-attempt': 0}

        def fulfill_ccj_api_request(_, uri, headers):
            assert uri == INMATE_URL
            ccj_api_requests['current-attempt'] += 1
            return 500, headers, expected_text

        httpretty.register_uri(httpretty.GET, COOK_COUNTY_JAIL_INMATE_DETAILS_URL,
                               body=fulfill_ccj_api_request)

        http = Http()
        okay, fetched_contents = http.get(INMATE_URL, number_of_attempts)

        assert not okay
        assert ccj_api_requests['current-attempt'] == ccj_api_requests['succeed-attempt']
        assert fetched_contents['status-code'] == 500

    def test_get_fails_no_such_place(self):
        inmate_url = 'http://idbvf3ruvfr3ubububufvubeuvdvd2uvuevvgud2bewhde.duucuvcryvgrfvyv'
        http = Http()
        okay, fetched_contents = http.get(inmate_url)

        assert not okay
        assert fetched_contents == BAD_URL_NETWORK_PROBLEM
