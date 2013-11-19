#
# Warning:
# ========
#   The python version available on the cookcountyjail.recoveredfactory.net
#   machine does not set load paths correctly so for the time being:
#      1) Do not add #! to this file.
#      2) invoke this from parent directory like this:
#             python scripts.scraper
#
# This scrapes the Cook County Jail website populating the 2.0 API
# system with the results of the scrapping.
#
# This is expected to run after the existing 1.0 API scraper has run,
# so the target date is 11am. If it runs at that time or later in the
# day then it fetches the sumarized date from yesterday, otherwise it
# fetches the info from the day before yesterday.
#


# select count(*) from countyapi_countyinmate
#   where booking_date < '2013-07-22' and
#   (discharge_date_earliest is null or
#    discharge_date_earliest >= '2013-07-21');

from datetime import datetime, timedelta
from summarize_daily_population import SummarizeDailyPopulation


#STARTING_DATE = '2013-07-22'
#DAY_BEFORE = str(datetime.strptime(STARTING_DATE, '%Y-%m-%d').date() - timedelta(1))

#
#COOK_COUNTY_URL = 'http://cookcountyjail.recoveredfactory.net'
#COOK_COUNTY_INMATE_API = '%s/api/1.0/countyinmate' % COOK_COUNTY_URL
#
#RACE_COUNTS = {'AS': 0, 'BK': 0, 'IN': 0, 'LT': 0, 'UN': 0, 'WH': 0}
#
#
#class SummarizeDailyPopulation:
#
#    def __init__(self):
#        self._change_counts = None
#        self.inmate_api = 'http://cookcountyjail.recoveredfactory.net/api/1.0/countyinmate?format=json&limit=1'
#        self.qualities = {
#            'M': 'males',
#            'AS': 'as',
#            'booked': 'booked'
#        }
#
#    @staticmethod
#    def _booked_males_as(response):
#        return len(loads(response.text)['objects'])
#
#    def build_starting_population(self):
#        get_cmd = '%s?format=json&limit=0&booking_date__lt=%s&discharge_date_earliest__isnull=True' % \
#                  (COOK_COUNTY_INMATE_API, STARTING_DATE)
#        not_discharged_response = requests.get(get_cmd)
#        assert not_discharged_response.status_code == 200
#        not_discharged_response = loads(not_discharged_response.content)
#        discharged_after_start_date_command = \
#            '%s?format=json&limit=0&booking_date__lt=%s&discharge_date_earliest__gte=%s' % \
#            (COOK_COUNTY_INMATE_API, STARTING_DATE, STARTING_DATE)
#        discharged_response = requests.get(discharged_after_start_date_command)
#        assert discharged_response.status_code == 200
#        discharged_response = loads(discharged_response.content)
#        inmates = copy(not_discharged_response['objects'])
#        inmates.extend(discharged_response['objects'])


now = datetime.today()
sdp = SummarizeDailyPopulation()
num_days_ago = timedelta(1 if now.hour >= 11 else 2)
sdp.summarize(str(now.date() - num_days_ago))
