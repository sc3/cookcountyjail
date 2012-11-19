# Cook County Jail Inmate Population tracker architecture roadmap

## Models

* Inmate: Name, charges, gender, intake date, discharge date, (other
  fields available on inmate site)
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

The front end will consist of Backbone components:

* Data views: Bind to JSON data and use D3 to visualize.
* Navigation app: Provide time selection and multiple views of data.
