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

from datetime import datetime, timedelta
from summarize_daily_population import SummarizeDailyPopulation

now = datetime.today()
sdpc = SummarizeDailyPopulation()
num_days_ago = timedelta(1 if now.hour >= 11 else 2)
sdpc.date(str(now.date() - num_days_ago))
