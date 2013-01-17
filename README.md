# Cook County Jail inmate tracker

A Django app that tracks the population of Cook County Jail over time
and summarizes trends.

# Using the API

See the [API guide](https://github.com/sc3/cookcountyjail/wiki/API-guide)
for accessing the production API service and querying the data.

# Running it locally

The scraper is invoked with a management command:

<pre>./manage.py scrape_inmates</pre>

<code>scrape_inmates</code> also supports a <code>--limit / -l</code>
flag which limits the number of records created and <code>--search /
-s</code> flag which overrides the default A-Z search strategy. 

# License

Licensed under the GNU General Public License Version 3.
See LICENSE.md.

# Contributors

See AUTHORS.md for contributors.
