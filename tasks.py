#
# Common Tasks associated with Cook Count Jail 2.0 API project.
#

from invoke import task, run
import pytest
import os


@task
def deploy():
    run('fab production deploy')


@task
def test_server():
    run('./manage.py')


@task
def tests():
    os.environ['TESTING'] = '1'
    pytest.main()
    os.environ['TESTING'] = '0'


@task
def update_software():
    run('pip install -U -r config/requirements.txt')
