#
# Common Tasks associated with Cook Count Jail 2.0 API project.
#

from invoke import task, run
import pytest, os


@task
def deploy():
    run('fab production deploy')


@task
def tests():
    os.environ['CCJ_TESTING'] = '1'
    pytest.main()
    os.environ['CCJ_TESTING'] = '0'
