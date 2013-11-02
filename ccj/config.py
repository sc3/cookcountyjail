import os
_basedir = os.path.abspath(os.path.dirname(__file__))

########################################################
#
# Settings are defined at the end of this file
#
#############################################

NEGATIVE_VALUES = set(['0', 'false'])


def get_db_uri():
    if use_postgres():
        db_config = {
            'dialect': 'postgresql',
            'db_user': 'cookcountyjail',
            'db_name': 'cookcountyjail_v2_0_dev',
            'pw': 'walblgadb;lgall',
            'host': 'localhost',
        }
        template = '%(dialect)s://%(db_user)s:%(pw)s@%(host)s/%(db_name)s'
    else:
        db_config = {
            'dialect': 'sqlite',
            'abs_path_to_db': '%s/ccj.db' % _basedir
        }
        template = '%(dialect)s:///%(abs_path_to_db)s'

    return (template % db_config)


def get_dpc_path():
    if in_production() and not in_testing():
        # production
        return '/home/ubuntu/website/2.0/db_backups/dpc.csv'
    elif in_testing():
        # testing
        return '/tmp/test.csv'
    else:
        # local development
        return '/tmp/dpc.csv'


def env_var_active(env_var):
    """
    Calculates if an environment variable is set.
    """
    env_var_value = os.environ.get(env_var)
    return env_var_value and env_var_value.lower() not in NEGATIVE_VALUES


def in_testing():
    """ Checks to see if we are testing the application. """
    return env_var_active('CCJ_TESTING')


def in_production():
    """
    Calculates if to run in production mode.
    If environment var CCJ_PRODUCTION != False or 0 or None, then in production mode.
    """
    return env_var_active('CCJ_PRODUCTION')


def use_postgres():
    """
    Calculates if Postgres database is to be used.
    If in production mode, then use Postgres.
    If environment var USE_POSTGRES != False or 0 or None, then use Postgres.
    """
    return in_production() or env_var_active('USE_POSTGRES')


IN_PRODUCTION = in_production()
IN_TESTING = in_testing()

if not in_production():
    DEBUG = True

SQLALCHEMY_DATABASE_URI = get_db_uri()
DPC_PATH = get_dpc_path()
