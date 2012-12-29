# Cook County Jail Inmate Population tracker

A Django app that tracks the population of Cook County Jail over time
and summarizes trends.

# Using it

There is currently no user interface or production website. You can run
the scraper and summarizer with two management commands:

<pre>./manage.py scrape_inmates
./manage generate_inmate_summaries</pre>

<code>scrape_inmates</code> also supports a <code>--limit / -l</code>
flag which limits the number of records created and <code>--search /
-s</code> flag which overrides the default A-Z search strategy. 

# Architecture roadmap

## Models

* Inmate: Name, charges, gender, intake date, discharge date, other
  fields available on inmate site (see a 
  [typical inmate record](http://www2.cookcountysheriff.org/search2/details.asp?jailnumber=2012-1013150)
  for details).
* Summaries: One or more models representing population summaries 
  (number of inmates, length of stay, distribution of charges and 
  demographics) by time period (day, week, month, quarter, year).


## Management commands

* `scrape_inmates`: Create inmate records by searching and scraping Cook
  County jail website.
* `generate_inmate_summaries`: Summarize data (number of inmates, length
  of stay, distribution of charges and demographics) by time period
(day, week, month, quarter, year)

## Views

A handful of views export JSON representing summaries by time period.

## Frontend

The front end will consist of Backbone components to be developed in 
January with the Chicago Data Visualization Group.

* Data views: Bind to JSON data and use D3 to visualize.
* Navigation app: Provide time selection and multiple views of data.

## Authors
Contributors: Ryan Asher, Cecilia Calaeria, David Eads, Jimmie Glover, Forest Gregg, Wilbero Morales, Sabine Ye
Licensed under the GPL version 3.
