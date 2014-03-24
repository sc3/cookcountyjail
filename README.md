# Cook County Jail Data Project

This repo backs a Django app that tracks the population of Cook County Jail over time and summarizes trends, the production version of which is currently running at http://cookcountyjail.recoveredfactory.net. We are also working on a Flask app to supplement and eventually replace the one currently available.

The application has three essential components: **(1) an API**, **(2) the database and models** that back the API, and **(3) the scraper** that populates the database.

## Using the API

For details on how to use the API we expose, see the [API guide](https://github.com/sc3/cookcountyjail/wiki/API-guide) for information on how to access the production API service and get a handle on our data.

### 2.0 API

The next generation of this API is currently under development. It is located on branch 2.0-dev. Documentation on what the API supports so far is located on the [API 2.0 Guide](https://github.com/sc3/cookcountyjail/wiki/API-2.0-Guide) page.

To request new functionality and to influence the choice of what API methods are built next, leave a comment on the [2.0 API Hackpad](http://is.gd/9tQpPj).

## The Data

Each day, a [scraper](https://github.com/sc3/cookcountyjail/wiki/Scraper) runs and updates our database of inmate information; personally identifying information is not kept. Over time, we have uncovered a lot of potentially interesting data that can be used to analyze trends in the Cook County Jail System. For a basic look at some of these trends, see our sister project, [26th and California](https://github.com/sc3/26thandcalifornia) and the site its running on: http://26thandcalifornia.recoveredfactory.net/v1.0/.  

## Setting up for development

Steps for getting started contributing are detailed below.

### Installation

First, you'll want to get a copy of this repository:

```
git clone git@github.com:sc3/cookcountyjail.git
```

### Running it locally

After you've checked out the source code repository, you need to install the requirements. You are strongly encouraged to create a [virtual environment](https://pypi.python.org/pypi/virtualenv) before installing them.

To install the requirements, you should have [pip](https://pypi.python.org/pypi/pip) installed. If you made a virtual environment, this is already done for you.

    pip install -r requirements.txt

By default, the locally running application uses the [sqlite](http://www.sqlite.org/) database, which is often already installed on modern operating systems. Assuming you have it available, you may now initialize the application database:

    ./manage.py syncdb --noinput
    ./manage.py migrate countyapi

### Cloning the database

Once you have setup your database the easiest way to populate it is to download the backup of the database that is made everyday after the Sheriff's website has been scraped. The URL to access this is:

    http://cookcountyjail.recoveredfactory.net/api/1.0/clone

This points to a gzipped JSON file of the database. Here is how to download the cloned copy of the database and use it to populate your database:

```
curl http://cookcountyjail.recoveredfactory.net/api/1.0/clone > /tmp/ccj_cloned_db.json.gz
gunzip /tmp/ccj_cloned_db.json.gz
./manage.py loaddata /tmp/ccj_cloned_db.json
rm /tmp/ccj_cloned_db.json
```

Note: loading your local database can take upwards of 10 minutes.

### Running the scraper locally

If you want to then keep your database up to date then you need to run the scraper to populate your database with the changed records. The command to run the scraper program is:

```
./manage.py scrape_inmates
```

Note that the Cook County Sheriff's department typically finishes updating the inmate records for the previous day at around 8:30 am. It is recommend that you collect the records after this time, otherwise you can get partial records.

<code>scrape_inmates</code> also supports a <code>--limit / -l</code>
flag which limits the number of records created and <code>--search /
-s</code> flag which overrides the default A-Z search strategy.

## Contributing

If, after setting up your local environment, you want to make contributions back to our project's code, you can do so. Please submit a pull request to this repository on the appropriate branch, either master or 2.0-dev. Github should tell you if your contribution is able to be merged automatically. Additionally, if you wait for around 3-5 minutes, [Travis](https://travis-ci.org), the continuous integration service, will verify whether your new code meets our requirements. Specifically, whether it passes our tests, and whether it is Py3 compatible.

### Testing

If you want to check these things for yourself, you can do both with the following command:

    python -3 -m py.test

See AUTHORS.md for other contributors.

## License

Licensed under the GNU General Public License Version 3.
See LICENSE.md.
