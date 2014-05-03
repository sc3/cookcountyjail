import os

SITE_STATIC_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
SITE_DIR = os.path.dirname(os.path.dirname(__file__))

NEGATIVE_VALUES = {'0', 'false'}


def env_var_active(env_var):
    """
    Calculates if an environment variable is set.
    """
    env_var_value = os.environ.get(env_var)
    return env_var_value and env_var_value.lower() not in NEGATIVE_VALUES


def in_production():
    """
    Calculates if to run in production mode.
    If environment var CCJ_PRODUCTION != False or 0 or None, then in production mode
    """
    return env_var_active('CCJ_PRODUCTION')


def use_postgres():
    """
    Calculates if Postgres database is to be used.
    If in production mode, then use Postgres
    if environment var USE_POSTGRES != False or 0 or None, then use Postgres
    """
    return in_production() or env_var_active('USE_POSTGRES')


if not in_production():
    DEBUG = True
    TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS


if use_postgres():
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'cookcountyjail',
            'USER': 'cookcountyjail',
            'PASSWORD': 'walblgadb;lgall',
            'HOST': '127.0.0.1',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(SITE_DIR, 'ccj')
        }
    }

# Time zone
TIME_ZONE = 'America/Chicago'

# Language
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# Internationalization.
USE_I18N = False

# Number and date localization.
USE_L10N = False

# Naive times are good by us
USE_TZ = False

# Media directory
MEDIA_ROOT = ''

# Media URL
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (SITE_STATIC_ROOT,)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'fft_#2hrw3y)z4wf35hio*%e**)#3-kja5p!1lcb+pa!#ha8hc'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'countyapi.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'countyapi.wsgi.application'

TEMPLATE_DIRS = (os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'))

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'countyapi',
    'tastypie',
    'south',
)

ALLOWED_POST_IPS = ['127.0.0.1']

ALLOWED_HOSTS = ['cookcountyjail.recoveredfactory.net']

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(levelname)s: %(message)s'
        },
    },
    'handlers': {
        'log_to_stdout': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'main': {
            'handlers': ['log_to_stdout'],
            'level': 'DEBUG',
            'propagate': True,
        }
    }
}
