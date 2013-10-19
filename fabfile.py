#
# Cook County Jail Fabric file for deploying V2.0 api.

from fabric.api import settings, env, prefix, cd, require, \
    run, sudo, hide
from fabric.contrib.files import exists
import sys


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
env.use_ssh_config = True

env.home = '/home/%(user)s' % env
env.venv = '%(home)s/.virtualenvs/%(project)s' % env
env.websites_path = '%(home)s/website/2.0/websites' % env
env.path = '%(websites_path)s/active' % env
env.config_dir = '%(path)s/config' % env
env.upstart_config_fname = '%(config_dir)s/upstart.conf' % env
env.cookcountyjail = 'cookcountyjail-2_0-dev'
env.cookcountyjail_config_fname = '/etc/init/%(cookcountyjail)s.conf' % env
env.repo = '%(home)s/repos/%(project)s_2.0-dev' % env
env.v2_0_dev_branch = 'v2.0-dev'
env.branch = env.v2_0_dev_branch
env.build_info_path = 'build_info'
env.current_build_id_path = '%(build_info_path)s/current' % env
env.previous_build_id_path = '%(build_info_path)s/previous' % env

######## Nginx Config #########

env.nginx_install_dir = '/etc/nginx/conf.d'

env.nginx_two_f = 'nginx-v2.conf'

env.nginx_two_conf = '%(config_dir)s/%(nginx_two_f)s' % env
env.nginx_two_inst = '%(nginx_install_dir)s/%(nginx_two_f)s' % env

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
    capture_latest_commit_id()
    create_latest_website()
    conditionally_update_restart_nginx()
    install_upstart_config()
    restart_gunicorn()


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


def capture_current_build_id():
    current_build_id_path = '%(path)s/%(current_build_id_path)s' % env
    if not exists(current_build_id_path):
        print('Error. Current installed website does not have a build_info/current file.')
        sys.exit(1)
    env.current_build_id = run('cat %s' % current_build_id_path)


def capture_latest_commit_id():
    with cd(env.repo):
        commit_str = 'commit '
        result = run('git log -1', quiet=True)
        index = result.find(commit_str) + len(commit_str)
        env.latest_commit_id = result[index:index + 10]


def capture_previous_build_id():
    previous_build_id_path = '%(path)s/%(previous_build_id_path)s' % env
    if exists(previous_build_id_path):
        env.previous_build_id = run('cat %s' % previous_build_id_path)
        return True
    return False


def create_path_to_new_website():
    env.new_website_path = '%(websites_path)s/%(latest_commit_id)s' % env


def checkout_latest():
    """Check out latest copy on a given branch."""
    std_requires()
    with cd(env.repo):
        run('git checkout %(branch)s' % env)
        run('git fetch')
        run('git pull')


def conditionally_update_restart_nginx():
    """
    Updates system nginx configuration file if it has changed and restarts nginx
    """
    if files_are_different(env.nginx_two_conf, env.nginx_two_inst):
        sudo_cp(env.nginx_two_conf, env.nginx_two_inst)
        restart_nginx()


def copy_repo_to_new_website():
    run('cp -R %(repo)s/* %(new_website_path)s' % env)


def create_latest_website():
    capture_current_build_id()
    create_path_to_new_website()
    if okay_to_install_new_website():
        create_new_website_directory()
        copy_repo_to_new_website()
        store_build_info()
        install_requirements()
        link_to_new_website(env.latest_commit_id)


def create_new_website_directory():
    run('mkdir -p %(new_website_path)s' % env)


def files_are_different(fname_a, fname_b):
    """Returns True if the two named files are different, False otherwise."""
    with settings(hide('warnings', 'stdout', 'stderr'), warn_only=True):
        result = run("diff -q '%s' '%s'" % (fname_a, fname_b))
        return result.return_code != 0


def install_requirements():
    """
    Install the required packages using pip.
    """
    std_requires()
    with activate_cmd():
        run('pip install -U -r %(new_website_path)s/config/requirements.txt' % env)


def install_upstart_config():
    """Install new gunicorn configuration file, if it has changed."""
    if files_are_different(env.upstart_config_fname, env.cookcountyjail_config_fname):
        sudo_cp(env.upstart_config_fname, env.cookcountyjail_config_fname)


def link_to_new_website(new_website_id):
    with cd(env.websites_path):
        run('rm -f active; ln -s %s active' % new_website_id)


def okay_to_install_new_website():
    return not exists('%(new_website_path)s' % env)


def remove_website(website_name):
    with cd(env.websites_path):
        run('rm -rf %s' % website_name)


def restart_nginx():
    """Restart nginx server."""
    std_requires()
    service_restart("nginx")


def restart_gunicorn():
    """Restart Python webserver that runs the Django server."""
    std_requires()
    service_restart(env.cookcountyjail)


def rollback():
    std_requires()
    if capture_previous_build_id():
        capture_current_build_id()
        link_to_new_website(env.previous_build_id)
        conditionally_update_restart_nginx()
        install_upstart_config()
        restart_gunicorn()
        remove_website(env.current_build_id)


def service_restart(service_name):
    """Restarts the named service. This service needs to be run in admin mode."""
    sudo("service %s restart" % service_name)


def service_stop(service_name):
    """Restarts the named service. This service needs to be run in admin mode."""
    sudo("service %s stop" % service_name)


def std_requires():
    require('settings', provided_by=[production])


def stop_gunicorn():
    """Restart Python webserver that runs the Django server."""
    std_requires()
    service_stop(env.cookcountyjail)


def store_build_info():
    with cd(env.new_website_path):
        run('mkdir %(build_info_path)s' % env)
        run('echo %(current_build_id)s > %(previous_build_id_path)s' % env)
        run('echo %(latest_commit_id)s > %(current_build_id_path)s' % env)


def sudo_cp(src_fname, trg_fname):
    """Copy file(s) to area that require admin level access."""
    sudo("cp '%s' '%s'" % (src_fname, trg_fname))
