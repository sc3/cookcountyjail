# Cook County Jail inmate tracker

A Django app that tracks the population of Cook County Jail over time
and summarizes trends.

# Using the API

See the [API guide](https://github.com/sc3/cookcountyjail/wiki/API-guide)
for accessing the production API service and querying the data.

# Setting up for local development
=======
# Installation

```
git clone git@github.com:sc3/cookcountyjail.git
cd cookcountyjail
pip install -r config/requirements.txt
```

# Running it locally

After you've checked out the source code repository, you need to install the requirements. You are strongly encouraged
to create a [virtual environment](https://pypi.python.org/pypi/virtualenv) before installing them.

To install the requirements, you should have `[pip](https://pypi.python.org/pypi/pip)` installed. If you made a virtual environment, this is already done for you.

    pip install -r config/requirements.txt

By default, the locally running application uses the `[sqlite](http://www.sqlite.org/)` database, which is often already installed on modern operating systems. Assuming you have it available, you may now initialize the application database:

    ./manage.py syncdb --noinput
    ./manage.py migrate countyapi

# Cloning the database

Once you have setup your database the easiest way to populate it is to download the backup of the
database that is made everyday after the Sheriff's website has been scrapped. The url to access this is:

    http://cookcountyjail.recoveredfactory.net/api/1.0/clone

This points to a gzipped JSON file of the database.

Here is how to download the cloned copy of the database and use it to populate your database:

```
curl http://cookcountyjail.recoveredfactory.net/api/1.0/clone > /tmp/ccj_cloned_db.json.gz
gunzip /tmp/ccj_cloned_db.json.gz
./manage.py loaddata /tmp/ccj_cloned_db.json
rm /tmp/ccj_cloned_db.json
```

Note: loading your local database can take upwords of 10 minutes.

# Running the scraper locally

If you want to then keep your database up to date then you need to run the scraper to populate
your database with the changed records. The command to run the scraper program is:

```
./manage.py scrape_inmates
```

Note that the Cook County Sheriff's department typically finishes updating the inmate records for the previous day
at around 8:30 am. It is recommend that you collect the records after this time, otherwise you can get partial
records.

Other useful commands
```
./manage.py check_inmate
./manage.py generate_datebase_audit_script
./manage.py generate_search_for_discharged_inmates_cmds
./manage.py generate_summaries
./manage.py inmate_details
./manage.py inmate_utils
./manage.py look_for_missing_inmates
./manage.py poll_inmates
./manage.py scrape_inmates
./manage.py utils
./manage.py validate_inmate_records
```

<code>scrape_inmates</code> also supports a <code>--limit / -l</code>
flag which limits the number of records created and <code>--search /
-s</code> flag which overrides the default A-Z search strategy.

# License

Licensed under the GNU General Public License Version 3.
See LICENSE.md.

# Contributors

See AUTHORS.md for contributors.
