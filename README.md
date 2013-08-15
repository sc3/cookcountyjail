# Cook County Jail inmate tracker

A Django app that tracks the population of Cook County Jail over time
and summarizes trends.

# Using the API

See the [API guide](https://github.com/sc3/cookcountyjail/wiki/API-guide)
for accessing the production API service and querying the data.

# Setting up for local development

After you've checked out the source code repository, you need to install the requirements. You are strongly encouraged
to create a [virtual environment](https://pypi.python.org/pypi/virtualenv) before installing them. 

To install the requirements, you should have `[pip](https://pypi.python.org/pypi/pip)` installed. If you made a virtual environment, this is already done for you.

    pip install -r requirements.txt

By default, the locally running application uses the `[sqlite](http://www.sqlite.org/)` database, which is often already installed on modern operating systems.

# Running the web application locally


# Running the scraper locally

The scraper is invoked with a management command:

    ./manage.py scrape_inmates

<code>scrape_inmates</code> also supports a <code>--limit / -l</code>
flag which limits the number of records created and <code>--search /
-s</code> flag which overrides the default A-Z search strategy. 

# License

Licensed under the GNU General Public License Version 3.
See LICENSE.md.

# Contributors

See AUTHORS.md for contributors.
