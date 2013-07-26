from datetime import date, timedelta
import logging
from django.core.management.base import BaseCommand

log = logging.getLogger('main')


class Command(BaseCommand):
    """
    This generates a shell script that will before a database audit.
    The audit program look like this:
        in parallel {validate_inmate_records from beginning time to yesterday}
        in parallel {look_for_missing_inmates from 2013-01-01 to yesterday}

    Both operations will take a lot of time, hence the
    use of parallelization for both of them.

    It would be better if the amount of parallelization was increased, but that
    requires significant more programming effort.
    """

    help = "%s%s" % ("Generates a script to perform a full audit of inmates ",
                     "against Cook Count Sherif's website.")

    CONCURRENT_MISSING_SEARCHES = 13
    DATE_FORMAT = '%Y-%m-%d'
    ONE_DAY = timedelta(1)

    def handle(self, *args, **options):
        self.header()
        self.inmates_record_validation()
        self.look_for_missing_inmates()
        self.flush_webserver_cache()

    def flush_webserver_cache(self):
        print('echo "Priming the cache"')
        print('find /var/www/cache -type f -delete')
        url = 'http://cookcountyjail.recoveredfactory.net/api/1.0/countyinmate/'
        curl_cmd = 'curl -v -L -G -s -o/dev/null -d "limit=0&format=%s" %s'
        for content_type in ['jsonp&callback=processJSONP', 'csv', 'json']:
            print(curl_cmd % (content_type, url))
        print('')

    def header(self):
        print("%s\n\n%s\n%s\n%s" %
              ("#!/bin/sh",
               "#",
               "# Audit Cook County Jail Inmate Database",
               "#"))
        print('')
        print("source /home/ubuntu/.virtualenvs/cookcountyjail/bin/activate")
        print("export CCJ_PRODUCTION=True")
        print('')

    def inmates_record_validation(self):
        command_start = "echo \"./manage.py validate_inmate_records"
        print("(")

        # process inmates from before 2000
        print("   %s -e '%s'\"" % (command_start, '1999-12-31'))

        # process inmates from before 2012
        start_and_end_dates = [
            ('2000-01-01', '2000-12-31'),
            ('2001-01-01', '2001-12-31'),
            ('2002-01-01', '2002-12-31'),
            ('2003-01-01', '2003-12-31'),
            ('2004-01-01', '2004-12-31'),
            ('2005-01-01', '2005-12-31'),
            ('2006-01-01', '2006-12-31'),
            ('2007-01-01', '2007-12-31'),
            ('2008-01-01', '2008-12-31'),
            ('2009-01-01', '2009-12-31'),
            ('2010-01-01', '2010-06-30'),
            ('2010-07-01', '2010-12-31'),
            ('2011-01-01', '2011-02-28'),
            ('2011-03-01', '2011-04-30'),
            ('2011-05-01', '2011-06-30'),
            ('2011-07-01', '2011-08-31'),
            ('2011-09-01', '2011-09-30'),
            ('2011-10-01', '2011-10-31'),
            ('2011-11-01', '2011-10-30'),
            ('2011-12-01', '2011-12-31'),
        ]
        for start_date, end_date in start_and_end_dates:
            print("   %s -s '%s' -e '%s'\"" %
                  (command_start, start_date, end_date))

        # process inmates from January 1st 2012 and on, one day at a time
        start_date = date(2012, 1, 1)
        end_date = date.today() - self.ONE_DAY
        while start_date <= end_date:
            cur_date = start_date.strftime(self.DATE_FORMAT)
            print("   %s -s '%s' -e '%s'\"" %
                  (command_start, cur_date, cur_date))
            start_date += self.ONE_DAY
        print(") | parallel -j %d" % self.CONCURRENT_MISSING_SEARCHES)
        print('')

    def look_for_missing_inmates(self):
        start_date = date(2013, 1, 1)
        end_date = date.today() - self.ONE_DAY
        print("(")
        while start_date <= end_date:
            print("   %s '%s'\"" %
                  ("echo \"./manage.py look_for_missing_inmates -d",
                   start_date.strftime(self.DATE_FORMAT)))
            start_date += self.ONE_DAY
        print(") | parallel -j %d" % self.CONCURRENT_MISSING_SEARCHES)
        print('')
