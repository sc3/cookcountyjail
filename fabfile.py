from fabric.api import settings, abort, run, cd, env, prefix
from fabric.contrib.console import confirm
import subprocess

# Some global variables. Need some tweaking to make them more modular
HOME = '~'
VIRTUALENV_NAME = 'countyjail' # change to desired name
VIRTUALENVS_DIRECTORY = '~/ENV' # change to the path where all the envs are gonna be stored
COOKCOUNTY_ENV_PATH = '%s/%s' % (VIRTUALENVS_DIRECTORY, VIRTUALENV_NAME) # where our env should be
PROJECT_PATH = '~/cookcountyjail' # change to where the project is located
SOURCE_CODE_SITE = 'https://github.com/sc3/cookcountyjail'

# Singleton enviorement for fabric itself, != our virtualenv
env.hosts = ['127.0.0.1'] # our localhost

def pre_requirements():
    """Stuff needed before it all like virtualenv before running project's pip install requirement.txt"""
    print "Installing pre-requisite modules and third-party software..."
    pre_reqs = ['python-virtualenv', 'python-setuptools', 'git']
    unfulfilled_reqs = ['libpq-dev', 'libxml2-dev', 'libxslt1-dev', 'python2.7-dev']
    # The above are all dependencies that pip was unable to resolve later on,
    # -- at least on the system that I tested this file.
    subprocess.call('sudo apt-get install ' + " ".join(unfulfilled_reqs + pre_reqs), shell=True)    

def install_project_requirements(file='requirements.txt'):
    run( start_env() + 'pip install -r %s' % file)

def create_env(env_name=VIRTUALENV_NAME, envs_path=VIRTUALENVS_DIRECTORY, home=HOME):
    """Make a vitualenv at the envs_path named env_name"""
    with cd(home):
        run('mkdir %s' % envs_path)
    with cd(envs_path):
        run('virtualenv --distribute %s' % env_name)
        
def start_env(env_path=COOKCOUNTY_ENV_PATH):
     """Function to activate the virtualenv warning only returns a string to be used and not
     actually runs the env"""
     return ('source %s/bin/activate && ' % env_path)
     
def clone_repo(repo_path=SOURCE_CODE_SITE):
     run('git clone %s' % repo_path)
     
def syncdb():
    run(start_env() + './manage.py syncdb')

def migrate(app):
    if not app:
        abort('Provide the app to be migrated')
    run(start_env()+'./manage.py migrate %s' % app)

def complete_setup():
    """ Mash up of all other setup functions"""
    print "Not ready"
    # May still not be ready for testing ... SEEMS to accept input for django user set up
    if not confirm("Warning this file is untested and incomplete. Do you want to continue? "):
        return
    pre_requirements()
    create_env()
    clone_repo()
    start_env()
    with cd(PROJECT_PATH):
        install_project_requirements()
        syncdb()
        migrate('countyapi')
