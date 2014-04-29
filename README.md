[![Build Status](https://travis-ci.org/sc3/cookcountyjail.svg?branch=v2.0-dev)](https://travis-ci.org/sc3/cookcountyjail)

# Cook County Jail inmate tracker V2.0

A web application that tracks the population of Cook County Jail over time
and summarizes trends.

One of the characteristics of the V2.0 version is that the quality of the
collected is a primary goal and so robustness and reliability of the running
system are primiary concerns and are reflected in the process used to get the
system up and running.

Another stratgey being used is to leverage the API 1.0 data as much as possible.
The first API methods will be summary ones, with the data being extracted using the
1.0 API. The summaries will be updated daily, at 11:00 am, which should be sufficient
time for the 1.0 API scraper to have run.

The [API 2.0 Guide](https://github.com/sc3/cookcountyjail/wiki/API-2.0-Guide) will
be updated as each new method is added.

To request new functionlity and to influence the choice of what new API method is
build next add to the [2.0 API Hackpad](http://is.gd/9tQpPj).

The current API method being worked on is:
* **Daily Popualation Changes** - summary by day of the number of womem and men, by race, who enter and leave the System

The remainder of this document describes the development methodology and choices.
As the system gets built up then this document will describe other aspects usually covered by
README documents.

# Tools

* Language: Python 2.75 or higher in the 2.X line
* Database: Postgres
* Web Framework: Flask
* Database ORM: SQLAlchemy
* Data Transfer Format: JSON
* Unit Test: py.test
* Automated Deployment Tool: Fabric
* Automation Tool: Invoke
* [Tracking Board](https://trello.com/b/dGpGzzSW/ccj-v2-0-dev)
    * If you need access to this board go to the [Hackpad](http://is.gd/9tQpPj) and request access.
    * Color Legend of cards on the board:
        * Purple: Feature
        * Green: Data User Story
        * Orange: Data Provider Story
        * Blue: Operation Story
        * Yellow: Story Subtask
        * Red: Defect

The original plan was to use Python 3, however the Python based deployment tools Fabric and Ansible do not work
with Python 3. Given that we wil be using an automated Python deployment tool, this restriction meant that we
had to down grade to Python 2.7. At the current time the latest version is 2.7.5, which is the required version
for this project. We will be using the -3 option when we run the system, so that we can make sure that our code
is complient with Python 3. Perhaps an ambitious person may work on changing some of the Open Source tools that
are not fully version 3 ready.

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
* Data User - this is the end user of the data
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
* Stories and Features must have tests
* Running in production
* API documentation updated

An information data model exists for this project and is located here:
* Requirements for [Information Model](Google Doc /document/d/1ZoY-R0deM8OUGtsLfyegqE-QMwnZBp3vmbMQ3eQcXcw/edit?usp=sharing)
* Design of [Information Model](Google Doc /drawings/d/1WAXGB1l5QcX_2XV5_VjvVNNxOO9UvGIh5jXgakNnICo/edit?usp=sharing)

This project has a sister project based on sc3/26thandcalifornia that will use the
API. Details on this project are XXXX (this is to filled in later).

# Directory Structure

* / - top level files, like this one
* /ccj - website code
    * /__init.py__
    * /templates
    * app.py - main entry point to application
    * /models - where all of the application code is located
* /config - where all the configuration files are located
* /scripts - scripts used to do other activities like scrape Cook County Sheriff's website
* /tests - tests stored here, both unit and BDD
* /AUTHORS.md - people who contributed to building this functionality
* /fabfile.py - Fabric tasks that deploy new website and launch it and roll it back on production server
* /gunicorn.sh - Bash script to run application usin Gunicorn Python based webserver
* /manage.py - task to do various operations with application
* /README.md - this file
* /tasks.py - Invoke tasks that


# Setting up for local development
=======

Remember the V2.0 development is being done on the v2.0-dev branch.

# Installation
Fork the sc3/cookcountyjail github repository

It is recommend that you use the virtualenv to work with this python project.

```
git clone git@github.com:<your github account>/cookcountyjail.git
cd cookcountyjail
git checkout v2.0-dev
pip install -U -r requirements.txt
```

#Usage

On development server:

```
python -3 manage.py -sdb
python -3 manage.py
```

#Testing

Whenever adding new functionality write tests. The first test file written,
test_postgres_db_installation.py, was run using nose, however since this
test can only be run on the production machine and since nose does not support
conditional execution nor a simple assertion syntax, test runner was changed to
py.test. A testing task was added to the set of Invoke tasks:

```
invoke tests
```

To run an individual test, useful when developing new functionality use the
following command:

```
invoke test -n tests/<test file name>
```

#Commiting code

Whenever you commit code please add the Vertical Slice id from the card on the
[Tracking Board](https://trello.com/b/dGpGzzSW/ccj-v2-0-dev) to the beginning
of the commit message, for example like this:

```
git commit -am 'VS 2.1.2 Fixed up documentation, correcting typos and adding missing section on committing code.'
```

The string, VS 2.1.2, indicates that the work is done against Story number 2 of Feature number 1 of
Vertical Slice 2. This card is easy to locate on the board.

#Automated Tasks

Projects like this have a number of tasks that people do that can be automated.
This project used the Python based tool, Invoke, to automated tasks. These tasks
are implemented in the, tasks.py, file. To find out the current set of tasks:

```
invoke -l
```

To run a task:

```
invoke <task name>
```

#Deploying

After a merge has happened on sc3/cookcountyjail project, the new version
is deployed using the automted deployment tool, Fabric, like this:

```
invoke deploy
```

This will call Fabric, which will in turn use git to fetch the latest
version of the website, then will extract the latest git commit id,
which is used to name the directory in ~/website/2.0/websites, which
the latest version of the website is stored. The automated install
script also updates requirements and if the Nginx configuration file
has been changed, installs and restarts Nginx. Then it restart gunicorn.
It also links the name active to the newly created dircetory.

#Rollback

If a newly released verison of the website causes problems, the website
can be reverted back to the previous version with the command:

```
fab production rollback
```

This command points the active driectory to the previous website vetrsion,
restarts Nginx if needed and then restart gunicorn which uses the previous
version and then the rollbacked version of the website is deleted from
the ~/website/2.0/websites dircetory, so it cannot be accidently used.

# License

Licensed under the GNU General Public License Version 3.
See LICENSE.md.

# Contributors

See AUTHORS.md for contributors.
