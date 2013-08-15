# Cook County Jail inmate tracker

A Django app that tracks the population of Cook County Jail over time
and summarizes trends.

# Using the API

See the [API guide](https://github.com/sc3/cookcountyjail/wiki/API-guide)
for accessing the production API service and querying the data.

# Installation

```
git clone git@github.com:sc3/cookcountyjail.git
cd cookcountyjail
pip install -r requirements.txt
```

# Running it locally

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

# License

Licensed under the GNU General Public License Version 3.
See LICENSE.md.

# Contributors

See AUTHORS.md for contributors.
