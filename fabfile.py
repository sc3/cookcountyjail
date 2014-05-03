from fabric.api import settings, abort, local, lcd, env, prefix, cd, require, \
    run, sudo, hide
from fabric.contrib.console import confirm
from fabric.contrib.files import exists
from datetime import date
from os.path import join as file_join


# Some global variables. Need some tweaking to make them more modular
HOME = '~'
VIRTUALENV_NAME = 'countyjail_env'  # change to desired name
VIRTUALENVS_DIRECTORY = '~/ENV'  # change to the path where all the envs are gonna be stored
COOKCOUNTY_ENV_PATH = '%s/%s' % (VIRTUALENVS_DIRECTORY, VIRTUALENV_NAME)  # where our env should be
PROJECT_PATH = '~/cookcountyjail'  # change to where the project is located
SOURCE_CODE_SITE = 'https://github.com/sc3/cookcountyjail'
WEBSITE = 'website'

"""
Base environment
"""

env.user = 'ubuntu'
env.project = 'cookcountyjail'
env.home = '/home/%(user)s' % env
env.venv = '%(home)s/.virtualenvs/%(project)s' % env
env.apps = '%(home)s/apps' % env
env.path = '%(apps)s/%(project)s' % env
env.static_files_dir = '%(path)s/static' % env
env.config_dir = '%(path)s/config' % env
env.backup_dirs = 'website/1.0/db_backups'

######## Upstart Config #########

env.upstart_conf = '%(config_dir)s/upstart.conf' % env
env.upstart_inst = '/etc/init/cookcountyjail.conf'

######## Nginx Config #########

env.nginx_install_dir = '/etc/nginx/conf.d'

env.nginx_one_f = 'nginx-v1.conf'
env.nginx_master_f = 'nginx.conf.master'

env.nginx_one_conf = '%(config_dir)s/%(nginx_one_f)s' % env
env.nginx_master_conf = '%(config_dir)s/%(nginx_master_f)s' % env
env.nginx_one_inst = '%(nginx_install_dir)s/%(nginx_one_f)s' % env
env.nginx_master_inst = '%(nginx_install_dir)s/%(nginx_master_f)s' % env

######## General Config ########

filesets = {
    'upstart': (env.upstart_conf, env.upstart_inst),
    'nginx_1': (env.nginx_one_conf, env.nginx_one_inst),
    'nginx_m': (env.nginx_master_conf, env.nginx_master_inst)
}

env.use_ssh_config = True

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

#
# Branches
#


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


#
# Deployment
#


def deploy():
    """Deploy code, run migrations, and restart services."""
    require('settings', provided_by=[production, staging])
    require('branch', provided_by=[stable, master, branch])

    add_directories()
    checkout_latest()
    install_requirements()
    run_migrations()
    try_update_all_config_files()
    restart_gunicorn()
    # Ask about bouncing the cache


def activate_cmd():
    return prefix('source %(venv)s/bin/activate' % env)


def add_directories():
    """
    Adds directories if needed
    """
    dirs = [WEBSITE, WEBSITE + '/1.0/db_backups/']
    for d in dirs:
        if not exists(d):
            run("mkdir -p '%s'" % d)


def checkout_latest():
    """Check out latest copy on a given branch."""
    require('settings', provided_by=[production, staging])
    require('branch', provided_by=[stable, master, branch])
    with cd(env.path):
        run('git fetch')
        run('git pull origin %(branch)s' % env)


def clear_cache():
    """
    Clears the Nginx cache
    """
    sudo('find /var/www/cache -type f -delete')


def files_are_different(fname_a, fname_b):
    """Returns True if the two named files are different, False otherwise."""
    with settings(hide('warnings', 'stdout', 'stderr'), warn_only=True):
        result = run("diff -q '%s' '%s'" % (fname_a, fname_b))
        return result.return_code == 1


def try_update_all_config_files():
    """
    Conditionally update all config files, and handle results.
    """
    _ = try_update_config_file('upstart')
    result2 = try_update_config_file('nginx_1')
    result3 = try_update_config_file('nginx_m')

    if result2 or result3:
        restart_nginx()


def try_update_config_file(which):
    """
    Conditionally update any one of multiple config files, as defined
    by 'filesets' variable
    """
    config, installed = filesets[which]
    if files_are_different(config, installed):
        sudo_cp(config, installed)
        return True
    return False


def install_requirements():
    """
    Install the required packages using pip.
    """
    require('settings', provided_by=[production, staging])
    require('branch', provided_by=[stable, master, branch])
    with activate_cmd():
        run('pip install -U -r %(path)s/requirements.txt' % env)


def run_migrations():
    require('settings', provided_by=[production, staging])
    require('branch', provided_by=[stable, master, branch])
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


def sudo_cp(src_fname, trg_fname):
    """Copy file(s) to area that require admin level access."""
    sudo("cp '%s' '%s'" % (src_fname, trg_fname))


def v1_static():
    """Links the 1.0 static files to main static file location."""
    with cd(WEBSITE):
        run("ln -sf '%(static_files_dir)s' static" % env)


#
# Install (@TODO refactor into server setup + local bootstrap)
#


def pre_requirements():
    """Stuff needed before it all like virtualenv before localning project's pip install requirement.txt"""
    print("Installing pre-requisite modules and third-party software...")
    pre_reqs = ['python-virtualenv', 'python-setuptools', 'git']
    unfulfilled_reqs = ['libpq-dev', 'libxml2-dev', 'libxslt1-dev', 'python2.7-dev']
    # The above are all dependencies that pip was unable to resolve later on,
    # -- at least for the system that I used to test this file.
    local('sudo apt-get install ' + " ".join(unfulfilled_reqs + pre_reqs))


def install_project_requirements(requirements_file='requirements.txt'):
    local('%s pip install -r %s' % (start_env(), requirements_file))


def create_env(env_name=VIRTUALENV_NAME, envs_path=VIRTUALENVS_DIRECTORY, home=env.home):
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
    return 'source %s/bin/activate && ' % env_path


def clone_repo(repo_path=SOURCE_CODE_SITE):
    local('git clone %s' % repo_path)


def dump_db():
    dump_db_file_name = 'cookcountyjail-%s.json' % str(date.today())
    target_file_path = file_join(env.home, file_join(env.backup_dirs, dump_db_file_name))
    with cd(env.path):
        with activate_cmd():
            run('python ./manage.py dumpdata countyapi > %s' % target_file_path)
    with cd(env.backup_dirs):
        run('gzip -f %s' % dump_db_file_name)
        run('rm -f latest.json.gz; ln -s %s.gz latest.json.gz' % dump_db_file_name)


def syncdb():
    local(start_env() + './manage.py syncdb')


def migrate(app):
    if not app:
        abort('Provide the app to be migrated')
    local(start_env() + './manage.py migrate %s' % app)


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
