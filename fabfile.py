#
# Cook County Jail Fabric file for deploying V2.0 api.

from fabric.api import *
from fabric.contrib.files import exists
import sys


"""
Base environment
"""

#
# Project Variables and Directories
env.user = 'ubuntu'
env.project = 'cookcountyjail'
env.home = '/home/%(user)s' % env
env.full_project = '%(project)s_2.0-dev' % env
env.cookcountyjail = '%(project)s-2_0-dev'
env.venv = '%(home)s/.virtualenvs/%(project)s' % env
env.websites_path = '%(home)s/website/2.0/websites' % env
env.active = '%(websites_path)s/active' % env
env.config_dir = '%(active)s/config' % env
env.nginx_two_repo = '%(config_dir)s/nginx-v2.conf' % env
env.upstart_repo = '%(config_dir)s/upstart.conf' % env
env.repo = '%(home)s/repos/%(full_project)s' % env

#
# Build Info
env.build_info_path = 'build_info'
env.current_build_id_path = '%(build_info_path)s/current' % env
env.previous_build_id_path = '%(build_info_path)s/previous' % env

#
# Installed Config
env.nginx_install_dir = '/etc/nginx/conf.d'
env.nginx_two_installed = '%(nginx_install_dir)s/nginx-v2.conf' % env
env.upstart_installed = '/etc/init/%(full_project)s.conf' % env

#
# Dev Variables
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


"""
Branches
"""

# the only branch this fabfile serves currently
env.branch = 'v2.0-dev'


"""
Deployment
"""


def deploy():
    """Deploy code, install changed config files, and restart services."""
    std_requires()
    checkout_latest()
    capture_latest_commit_id()
    create_latest_website()
    try_update_all_config_files()
    restart_gunicorn()


def rollback():
    """ Revert to the previous build of the website, re-set config files,
        and delete the version of the website from which we have backed off. """
    std_requires()
    if capture_previous_build_id():
        capture_current_build_id()
        link_to_new_website(env.previous_build_id)
        try_update_all_config_files()
        restart_gunicorn()
        remove_website(env.current_build_id)


def activate_cmd():
    """ wrapper command to activate virtualenv with a context manager construct, 
        such as: 'with activate_cmd(): ...' """
    return prefix('source %(venv)s/bin/activate' % env)


def build_path_to_new_website():
    """ concatenate path for new website """
    env.new_website_path = '%(websites_path)s/%(latest_commit_id)s' % env


def capture_current_build_id():
    """ read the build info that is saved in production repo into Fabric's 
        env variable """
    current_build_id_path = '%(active)s/%(current_build_id_path)s' % env
    if not exists(current_build_id_path):
        sys.exit('Error. Current installed website does not have a build_info/current file.')
    env.current_build_id = run('cat %s' % current_build_id_path)


def capture_latest_commit_id():
    """ Store value of the latest commit id (the first 10 digits of it, anyway)
        in Fabric's env variable """
    with cd(env.repo):
        result = run('git show --pretty=%h --abbrev=10', pty=False)
        env.latest_commit_id = result


def capture_previous_build_id():
    """ Store the id of the last website build, if there was one. 
        Return True if there was, False otherwise. """
    previous_build_id_path = '%(active)s/%(previous_build_id_path)s' % env
    if exists(previous_build_id_path):
        env.previous_build_id = run('cat %s' % previous_build_id_path)
        return True
    return False


def checkout_latest():
    """Check out latest copy on a given branch."""
    std_requires()
    with cd(env.repo):
        run('git checkout %(branch)s' % env)
        run('git fetch')
        run('git pull')


def copy_repo_to_new_website():
    """ copy the newest git repo to path of new website build """
    run('cp -R %(repo)s/* %(new_website_path)s' % env)


def create_latest_website():
    """ Store value of the latest build id, create a new directory under websites
        for latest deployment, store build info, update reqs"""
    capture_current_build_id()
    build_path_to_new_website()
    if okay_to_install_new_website():
        create_new_website_directory()
        copy_repo_to_new_website()
        store_build_info()
        install_requirements()
        link_to_new_website(env.latest_commit_id)


def create_new_website_directory():
    """ create directory path to location of newest website build """
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


def link_to_new_website(new_website_id):
    """ move the 'active' pointer to the new supplied website """
    with cd(env.websites_path):
        run('rm -f active; ln -s %s active' % new_website_id)


def okay_to_install_new_website():
    """ return False if the new website directory already exists, True otherwise """
    return not exists('%(new_website_path)s' % env)


def remove_website(website_name):
    """ delete the directory containing the latest website"""
    with cd(env.websites_path):
        run('rm -rf %s' % website_name)


def restart_nginx():
    """Restart nginx server."""
    service_restart("nginx")


def restart_gunicorn():
    """Restart Gunicorn webserver on which the Flask app runs."""
    service_restart(env.full_project)


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
    """ create a 'build_info' directory inside location of new website
        and populate it with two files: 'current' and 'previous', containing 
        commit ids pointing to the current website, and the last website, 
        respectively. """
    with cd(env.new_website_path):
        run('mkdir %(build_info_path)s' % env)
        run('echo %(current_build_id)s > %(previous_build_id_path)s' % env)
        run('echo %(latest_commit_id)s > %(current_build_id_path)s' % env)


def std_requires():
    """ Requires that any function containing this call must also 
        call 'production', to get the 'settings' variable. """
    require('settings', provided_by=[production])


def sudo_cp(src_fname, trg_fname):
    """Copy file(s) to area that require admin level access."""
    sudo("cp '%s' '%s'" % (src_fname, trg_fname))


def try_update_all_config_files():
    """
    Update all installed config files whose repo versions 
    have changed, then handle results.
    """
    filesets = {
        'upstart': (env.upstart_repo, env.upstart_installed),
        'nginx_2': (env.nginx_two_repo, env.nginx_two_installed),
    }

    # iterate over config files
    diffs = {}
    for name, fileset in filesets.items():
        diffs[name] = try_update_file(*fileset)
    
    # Handle results
    if diffs['nginx_2']:
        restart_nginx()


def try_update_file(config, installed):
    """
    Update an installed version of a file if the repo's 
    copy of the file has changed.
    """
    if files_are_different(config, installed):
        sudo_cp(config, installed)
        return True
    return False
