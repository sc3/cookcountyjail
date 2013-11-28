#
# Common Tasks associated with Cook County Jail 2.0 API project.
#

from invoke import task, run
import pytest
import os
from contextlib import contextmanager


@task
def clean():
    run('find . -type f -name "*.pyc" -exec rm -f {} \;')


@task
def deploy():
    run('fab production deploy')


@task
def scraper():
    with _TestModeOn():
        run('python -3 scripts/scraper.py')


@task
def test_server():
    """
    Runs the server with testing mode on
    """
    with _TestModeOn():
        run('python -3 manage.py')


@task
def test(name=''):
    if name != '':
        with _TestModeOn():
            pytest.main(name)


@task
def tests():
    with _TestModeOn():
        run('python -3 -m py.test')


@task
def update_software():
    run('pip install -U -r config/requirements.txt')


# Helper functions


@contextmanager
def _TestModeOn():
    try:
        os.environ['CCJ_TESTING'] = '1'
        yield
    finally:
        os.environ['CCJ_TESTING'] = '0'
