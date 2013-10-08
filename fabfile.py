from fabric.api import settings, abort, local, lcd, env, prefix, cd, require, \
    run, sudo, hide
from fabric.contrib.console import confirm
from fabric.contrib.files import exists
import subprocess

# Some global variables. Need some tweaking to make them more modular
HOME = '~'
VIRTUALENV_NAME = 'countyjail_env'  # change to desired name
VIRTUALENVS_DIRECTORY = '~/ENV'  # change to the path where all the envs are gonna be stored
COOKCOUNTY_ENV_PATH = '%s/%s' % (VIRTUALENVS_DIRECTORY, VIRTUALENV_NAME)  # where our env should be
PROJECT_PATH = '~/cookcountyjail'  # change to where the project is located
SOURCE_CODE_SITE = 'https://github.com/sc3/cookcountyjail'
WEBSITE = 'website'
WEBSITES = WEBSITE + 's'


#"~/repos/cookcountyjail_2.0-dev"
# git log -1 --pretty="%H"


"""
Base environment
"""
env.user = 'ubuntu'
env.project = 'cookcountyjail'
env.home = '/home/%(user)s' % env
env.venv = '%(home)s/.virtualenvs/%(project)s' % env
env.apps = '%(home)s/apps' % env
env.path = '%(apps)s/%(project)s' % env
env.config_dir = '%(path)s/config' % env
env.use_ssh_config = True
env.nginx_conf_fname = '%(config_dir)s/nginx.conf' % env
env.installed_nginx_fname = '/etc/nginx/sites-available/cookcountyjail.conf'
env.static_files_dir = '%(path)s/templates' % env
env.upstart_config_fname = '%(config_dir)s/upstart.conf' % env
env.cookcountyjail_config_fname = '/etc/init/cookcountyjail.conf'
env.repo = '%(home)s/repos/%(project)s_2.0-dev'
env.v2_0_dev_branch = 'v2.0-dev'
env.branch = env.v2_0_dev_branch

"""
Environments
"""


def production():
    """
    Work on production environment
    """
    env.settings = 'production'
    env.hosts = ['cookcountyjail.recoveredfactory.net']


"""
Branches
"""


"""
Deployment
"""


def deploy():
    """Deploy code, run migrations, and restart services."""
    std_requires()

    add_directories()
    checkout_latest()
    # install_requirements()
    # run_migrations()
    # conditionally_update_restart_nginx()
    # install_upstart_config()
    # restart_gunicorn()
    # Ask about bouncing the cache


def activate_cmd():
    return prefix('source %(venv)s/bin/activate' % env)


def add_directories():
    """
    Adds directories if needed
    """
    dirs = [WEBSITE, WEBSITE + '/2.0/db_backups/', WEBSITE + '/2.0/' + WEBSITES]
    for d in dirs:
        if not exists(d):
            run("mkdir -p '%s'" % d)


def checkout_latest():
    """Check out latest copy on a given branch."""
    std_requires()
    with cd(env.repo):
        run('git checkout %(branch)s' % env)
        run('git pull origin %(branch)s' % env)


def conditionally_update_restart_nginx():
    """
    Updates system nginx configuration file if it has changed and restarts nginx
    """
    if nginx_conf_file_updated():
        update_nginx_configuration()
        restart_nginx()


def files_are_different(fname_a, fname_b):
    """Returns True if the two named files are different, False otherwise."""
    with settings(hide('warnings', 'stdout', 'stderr'), warn_only=True):
        result = run("diff -q '%s' '%s'" % (fname_a, fname_b))
        return result.return_code == 1


def install_requirements():
    """
    Install the required packages using pip.
    """
    std_requires()
    with activate_cmd():
        run('pip install -U -r %(config_dir)s/requirements.txt' % env)


def install_upstart_config():
    """Install new gunicorn configuration file, if it has changed."""
    if files_are_different(env.upstart_config_fname, env.cookcountyjail_config_fname):
        sudo_cp('%(upstart_config_fname)s %(cookcountyjail_config_fname)s' % env)


def nginx_conf_file_updated():
    """Returns True if local nginx configuration file different from system one."""
    return files_are_different(env.nginx_conf_fname, env.installed_nginx_fname)


def run_migrations():
    std_requires()
    with activate_cmd():
        run('%(path)s/manage.py migrate' % env)


def restart_nginx():
    """Restart nginx server."""
    service_restart("nginx")


def restart_gunicorn():
    """Restart Python webserver that runs the Django server."""
    service_restart("cookcountyjail")


def service_restart(service_name):
    """Restarts the named service. This service needs to be run in admin mode."""
    sudo("service %s restart" % service_name)


def std_requires():
    require('settings', provided_by=[production])


def sudo_cp(src_fname, trg_fname):
    """Copy file(s) to area that require admin level access."""
    sudo("cp '%s' '%s'" % (src_fname, trg_fname))


def update_nginx_configuration():
    """Copies the nginx configuration file to system area."""
    sudo_cp(env.nginx_conf_fname, env.installed_nginx_fname)


def v1_static():
    """Links the 1.0 static files to main static file location."""
    with cd(WEBSITE):
        run("ln -sf '%(static_files_dir)s' static" % env)


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
    print("Not ready")
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
