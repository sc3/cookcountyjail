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
pip install -r requirements.txt
```

# Running it locally

After you've checked out the source code repository, you need to install the requirements. You are strongly encouraged
to create a [virtual environment](https://pypi.python.org/pypi/virtualenv) before installing them.

To install the requirements, you should have `[pip](https://pypi.python.org/pypi/pip)` installed. If you made a virtual environment, this is already done for you.

    pip install -r requirements.txt

By default, the locally running application uses the `[sqlite](http://www.sqlite.org/)` database, which is often already installed on modern operating systems. Assuming you have it available, you may now initialize the application database:

    ./manage.py syncdb --noinput
    ./manage.py migrate countyapi

# Running the scraper locally

Once you've set up the database, you need to run the scraper to populate the database with records.
The scraper is invoked with a management command:

```
./manage.py scrape_inmates
```

Other useful commands
```
./manage.py check_inmate
./manage.py clone_db
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

# Cloning the database

Everyday after the Sheriff's website has been scrapped a dump of the database
is made that is available for downloading. The url to access this copy is:

    [http://cookcountyjail.recoveredfactory.net/api/1.0/clone](http://cookcountyjail.recoveredfactory.net/api/1.0/clone)

The name of the file downloaded is clone and it is JSON file.


# License

Licensed under the GNU General Public License Version 3.
See LICENSE.md.

# Contributors

See AUTHORS.md for contributors.
