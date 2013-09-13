# Cook County Jail inmate tracker V2.0

A web application that tracks the population of Cook County Jail over time
and summarizes trends.

One of the characteristics of the V2.0 version is that the quality of the
collected is a primary goal and so robustness and reliability of the running
system are primiary concerns and are reflected in the process used to get the
system up and running.

At this point this document will only describe the development methodology and choices.
As the system gets built up then this document will describe other aspects usually covered by
README documents.

# Tools

* Language: Python 3.3.2 or higher
* Database: Postgres
* Web Framework: Flask
* Database ORM: SQLAlchemy
* Data Transfer Format: JSON
* Unit Test: ???
* BDD: ???
* Tracking Board: https://trello.com/b/dGpGzzSW/ccj-v2-0-dev
** If you need access to this board go to ????(need to have a request form on the net) and
request access.
** Legend of cards on the board
*** Purple: Feature
*** Green: Data User Story
*** Orange: Data Provider Story
*** Blue: Operation Story
*** Yellow: Story Subtask
*** Red: Defect

# Development Strategy

Vertical slices of functionality that are *done* when they are running in production mode
on http://cookcountyjail.recoveredfactory.net system and the functionality is accessed
through the following http://cookcountyjail.recoveredfactory.net/api/2.0/xxxx,
where xxxx is the specific API name and arguments.

While the release system will be running in Production mode, the data being collected
is not autoritative, the 1.0 API is authorative source of data, until a cut over occurs.
The date of the cutover is unknown at this point. It is important to repeat that while
the date is not authortative the processes and the release code is.

For the initial part of the development there will be only one vertical slice being developed
at a time. Once sufficient functionality has been developed additional vertical slices
targeting summary functionality can be developed in parallel.

There are three main users who will have stories in a vertical slice, they are:
* Data User -
* Data Producer - this covers the scraper, data migration and possibly integration from
other data sources
* Operations - this covers making monitoring that the system is running correctly and if
it does not how to detect and notify and find out information on the source of the problem

Not every vertical slice will have stories from all three users and it is expected that the
early ones will.

Also all features and stories will have automated tests to show that they work correctly.

## Definiton of Done
A vertical slice of funcitonality and stories will not be done until all of the following
conditions are met:
* Code must have unit tests
* Stories and Features must have BDD tests
* Running in production

An information data model exists for this project and is located here:
* Requirements for Information Model: Google Doc /document/d/1ZoY-R0deM8OUGtsLfyegqE-QMwnZBp3vmbMQ3eQcXcw/edit?usp=sharing
* Desing of Information Model: Google Doc /drawings/d/1WAXGB1l5QcX_2XV5_VjvVNNxOO9UvGIh5jXgakNnICo/edit?usp=sharing

This project has a sister project based on sc3/26thandcalifornia that will use the
API. Details on this project are XXXX (this is to filled in later).

# Directory Structure

* / - top level files, like this one
* /ccj - website code
** /__init.py__
** /templates
** appy.py - main entry point to application
** /models - where all of the application code is located
* /scripts - scripts used to do other activities like scrape Cook County Sheriff's website
* /tests - tests stored here, both unit and BDD


# Setting up for local development
=======

Remember the V2.0 development is being done on the v2.0-dev branch.

# Installation
Fork the sc3/cookcountyjail github repository

It is recommend that you use the virtualenv to work with this python project.

```
git clone git@github.com:&lt;your github account&gt;/cookcountyjail.git
cd cookcountyjail
git checkout v2.0-dev
pip install -r requirements.txt
```

#Usage

On development server:

```
python manage.py -sdb
python manage.py
```

On production servers: 

You already have Gunicorn if you installed the requirements.txt. Get Nginx
with ``` sudo apt-get install nginx ``` or an equivalent command. 

Make sure ports 80 and 8000 are both open, with: 
``` sudo fuser -n tcp <port-number> ```

If something is running, take the pid number(s) given, and call:
``` sudo kill <first-pid> <second-pid> ... ```

Run gunicorn server as defined in gunicorn.sh
``` source gunicorn.sh ```

Run nginx server with configurations defined in nginx.conf
``` sudo /usr/sbin/nginx -c nginx.conf ```

You should now be able to see the app at localhost.

# License

Licensed under the GNU General Public License Version 3.
See LICENSE.md.

# Contributors

See AUTHORS.md for contributors.
