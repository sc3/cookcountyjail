from fabric.api import settings, abort, local, lcd, env, prefix, cd, require, \
    run, sudo
from fabric.contrib.console import confirm
import subprocess

# Some global variables. Need some tweaking to make them more modular
HOME = '~'
VIRTUALENV_NAME = 'countyjail_env'  # change to desired name
VIRTUALENVS_DIRECTORY = '~/ENV'  # change to the path where all the envs are gonna be stored
COOKCOUNTY_ENV_PATH = '%s/%s' % (VIRTUALENVS_DIRECTORY, VIRTUALENV_NAME)  # where our env should be
PROJECT_PATH = '~/cookcountyjail'  # change to where the project is located
SOURCE_CODE_SITE = 'https://github.com/sc3/cookcountyjail'

"""
Base environment
"""
env.user = 'ubuntu'
env.project = 'cookcountyjail'
env.home = '/home/%(user)s' % env
env.venv = '%(home)s/.virtualenvs/%(project)s' % env
env.path = '%(home)s/apps/%(project)s' % env

"""
Environments
"""
def production():
    """
    Work on production environment
    """
    env.settings = 'production'
    env.hosts = ['cookcountyjail.recoveredfactory.net']


def staging():
    """
    Work on staging environment
    """
    env.settings = 'staging'
    env.hosts = ['cookcountyjail.beta.recoveredfactory.net']


"""
Branches
"""
def stable():
    """
    Work on stable branch.
    """
    env.branch = 'stable'


def master():
    """
    Work on development branch.
    """
    env.branch = 'master'


def branch(branch_name):
    """
    Work on any specified branch.
    """
    env.branch = branch_name


"""
Deployment
"""
def deploy():
    """Deploy code, run migrations, and restart services."""
    require('settings', provided_by=[production, staging])
    require('branch', provided_by=[stable, master, branch])

    checkout_latest()
    install_requirements()
    run_migrations()
    install_nginx_config()
    install_upstart_config()
    restart_nginx()
    restart_gunicorn()
    # Ask about bouncing the cache


def checkout_latest():
    """Check out latest copy on a given branch."""
    require('settings', provided_by=[production, staging])
    require('branch', provided_by=[stable, master, branch])

    with cd(env.path):
        run('git fetch')
        run('git pull origin %(branch)s' % env)


def install_requirements():
    """
    Install the required packages using pip.
    """
    require('settings', provided_by=[production, staging])
    require('branch', provided_by=[stable, master, branch])
    with prefix('source %(venv)s/bin/activate' % env):
        run('pip install -U -r %(path)s/requirements.txt' % env)


def run_migrations():
    require('settings', provided_by=[production, staging])
    require('branch', provided_by=[stable, master, branch])
    with prefix('source %(venv)s/bin/activate' % env):
        run('%(path)s/manage.py migrate' % env)


def install_nginx_config():
    """Install new nginx configuration file."""
    sudo("cp %(path)s/nginx.conf /etc/nginx/sites-available/cookcountyjail.conf" % env)
    pass


def install_upstart_config():
    """Install new gunicorn configuration file."""
    sudo("cp %(path)s/upstart.conf /etc/init/cookcountyjail.conf" % env)


def restart_nginx():
    """Restart nginx server."""
    sudo("service nginx restart")


def restart_gunicorn():
    sudo("service cookcountyjail restart")

#def bounce_cache(

"""
Install (@TODO refactor into server setup + local bootstrap)
"""
def pre_requirements():
    """Stuff needed before it all like virtualenv before localning project's pip install requirement.txt"""
    print("Installing pre-requisite modules and third-party software...")
    pre_reqs = ['python-virtualenv', 'python-setuptools', 'git']
    unfulfilled_reqs = ['libpq-dev', 'libxml2-dev', 'libxslt1-dev', 'python2.7-dev']
    # The above are all dependencies that pip was unable to resolve later on,
    # -- at least for the system that I used to test this file.
    subprocess.call('sudo apt-get install ' + " ".join(unfulfilled_reqs + pre_reqs), shell=True)


def install_project_requirements(file='requirements.txt'):
    local('%s pip install -r %s' % (start_env(), file))


def create_env(env_name=VIRTUALENV_NAME, envs_path=VIRTUALENVS_DIRECTORY, home=HOME):
    """Make a vitualenv at the envs_path named env_name"""
    with lcd(home):
        local('mkdir %s' % envs_path)
    with lcd(envs_path):
        local('virtualenv --distribute %s' % env_name)


def start_env(env_path=COOKCOUNTY_ENV_PATH):
    """
    Function to activate the virtualenv warning only returns a string to be used and not
    actually locals the env
    """
    return ('source %s/bin/activate && ' % env_path)


def clone_repo(repo_path=SOURCE_CODE_SITE):
    local('git clone %s' % repo_path)


def syncdb():
    local(start_env() + './manage.py syncdb')


def migrate(app):
    if not app:
        abort('Provide the app to be migrated')
    local(start_env()+'./manage.py migrate %s' % app)


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
    with lcd(PROJECT_PATH):
        install_project_requirements()
        syncdb()
        migrate('countyapi')


