#
# Common Tasks associated with Cook Count Jail 2.0 API project.
#

from invoke import task, run
import pytest


@task
def deploy():
    run('fab production deploy')


@task
def tests():
    pytest.main()
