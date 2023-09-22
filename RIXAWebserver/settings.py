import logging
from pathlib import Path
from django.utils.translation import gettext_lazy as _

import os
from decouple import Config, RepositoryEnv, Csv, Choices
from warnings import warn

import plugins.log_helper

DOC_BUILD = "BUILD_DOCS" in os.environ and os.environ["BUILD_DOCS"] == "True"

try:
    config_dir = os.environ["RIXA_WD"]
except KeyError:
    current_directory = os.getcwd()
    files = os.listdir(current_directory)
    if "config.ini" in files:
        config_dir = current_directory
    else:
        raise Exception(
            f"The folder '{current_directory}' from which you started the server does not seem to be a RIXA working directory."
            f"Either change into a working dir or set the 'RIXA_WD' env var.")

# check for wd conformity
if not DOC_BUILD:
    for dir in ["plugins", "plugin_configurations", "log"]:
        full_path = os.path.join(config_dir, dir)
        if not os.path.exists(full_path):
            try:
                os.mkdir(full_path)
            except Exception as e:
                print(e)
                raise Exception(f"Your working dir is missing the '{dir}' folder. Automatic fixing has failed. "
                                f"Is the working dir read only?")



config = Config(RepositoryEnv(os.path.join(config_dir, "config.ini")))
WORKING_DIRECTORY = os.path.abspath(config_dir)

try:
    secret_config = Config(RepositoryEnv(os.path.join(config_dir, "secret_config.ini")))
    OPENAI_API_KEY = secret_config("OPENAI_API_KEY", default="NONE")
except:
    warn("No config for secret keys defined!. Loading could fail")

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

"""The absolute path to the working directory (wd). If you want to change this via envvar use RIXA_WD.
"""
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/


SECRET_KEY = config("SECRET_KEY")  # 'django-insecure-nu#k(39g*22%6=!el+pz(qe3(7!$cj_wbs4845t2@73c7f#rtg'
"""SECURITY WARNING: keep the secret key used in production secret!
"""
DEBUG = config("DEBUG", default=False, cast=bool)
"""SECURITY WARNING: don't run with debug turned on in production!
"""
MAINTENANCE_MODE = config("MAINTENANCE_MODE", default=True, cast=bool)
"""prevents access to server outside of localhost. With asgi blocks all connections.
"""

ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())
"""List of domains which the webserver serves. '*' means all connections will be accepted.
Needs to be properly configured before deploying.
"""

# do not touch
INSTALLED_APPS = [
    'daphne',
    'account_managment.apps.AccountManagmentConfig',
    'dashboard.apps.DashboardConfig',
    'plugins.apps.PluginsConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'bootstrap5',
    'rosetta',

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'account_managment.visit_statistics.SimpleMiddleware'

]

ROOT_URLCONF = 'RIXAWebserver.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGI_APPLICATION = 'tipsy_tales.wsgi.application'
ASGI_APPLICATION = "RIXAWebserver.asgi.application"

# change to redis before deployment
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

# change before deployment
#
DATABASES = {
    'default': {
        'ENGINE': config("DB_ENGINE", default="django.db.backends.sqlite3"),
        'NAME': config("DB_NAME", default=os.path.join(config_dir ,'db.sqlite3'))
    }
}
"""https://docs.djangoproject.com/en/4.1/ref/settings/#databases
"""

# maybe uncomment some before deploying

_full_password_validation = [{'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
                             {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
                             {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
                             {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', }, ]
_use_password_validation = config("FULL_PASSWORD_VALIDATION", default=True, cast=bool)
AUTH_PASSWORD_VALIDATORS = _full_password_validation if _use_password_validation else []

# Availabe: main, materia, slate, morph, vapor, cyborg
BOOTSTRAP_THEME = config("BOOTSTRAP_THEME", default="materia")
#
# see https://bootswatch.com/
# available_bootstrap_themes = {"materia": "https://bootswatch.com/5/materia/bootstrap.min.css",
#                               "slate": "https://bootswatch.com/5/slate/bootstrap.min.css",
#                               "morph": "https://bootswatch.com/5/morph/bootstrap.min.css",
#                               "vapor": "https://bootswatch.com/5/vapor/bootstrap.min.css",
#                               "cyborg": "https://bootswatch.com/5/cyborg/bootstrap.min.css"}
# """available base css files. choice has no impact on layout of website. just changes colorscheme, button look etc.
# UNDER NO CIRCUMSTANCE use outside of dev as content server is not designated for supply
# """
# BOOTSTRAP5 = {
#     "css_url": available_bootstrap_themes[BOOTSTRAP_THEME]
# }
"""Set actual css theme. Use BOOTSTRAP_THEME in config file for changing
"""

# https://docs.djangoproject.com/en/4.1/topics/i18n/
LANGUAGE_CODE = 'en'
LANGUAGES = (
    ('en', _('English')),
    ('de', _('German')),
)
"""Internationalization.
I strongly recommend not changing any of this as it will break the entire site
"""

TIME_ZONE = config("TIME_ZONE", default="Europe/Berlin")

USE_I18N = True
USE_TZ = True
USE_L10N = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/
# needs to be switched before deploying
STATIC_ROOT = config("STATIC_ROOT", default = None)
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / "static"
]

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", default=False, cast=bool)
"""Make site work without SSL
"""
SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", default=False, cast=bool)
"""Make site work without SSL
"""
CSRF_COOKIE_SAMESITE = config("CSRF_COOKIE_SAMESITE", default='Lax', cast=Choices(["None", "Lax", "Strict"]))
"""Make site work without SSL
"""
SESSION_COOKIE_SAMESITE = config("SESSION_COOKIE_SAMESITE", default='Lax', cast=Choices(["None", "Lax", "Strict"]))
"""Make site work without SSL
"""

ROSETTA_SHOW_AT_ADMIN_PANEL = True
ROSETTA_EXCLUDED_APPLICATIONS = ('django.contrib.admin')

SESSION_EXPIRE_AT_BROWSER_CLOSE = config("SESSION_EXPIRE_AT_BROWSER_CLOSE", default=False, cast=bool)
SESSION_COOKIE_AGE = config("SESSION_COOKIE_AGE", default=60 * 60 * 24 * 14, cast=int)
"""Time in seconds before session is marked as invalid
"""

AUTH_USER_MODEL = 'account_managment.User'

LOGIN_URL = "account_user_login"

logfile_path = config("LOG_LOC", default="log/main")
"""Where logfile is located. Without starting `/` it is considered relative to the working directory.
"""
LOG_FILE_TYPE = config("LOG_FILE_TYPE", default="html", cast=Choices(["none", "html", "txt"]))
"""Either none, html or txt. None means no log files are created. html supports color formatting while. 
"""
if LOG_FILE_TYPE != "none" and logfile_path[0] != "/":
    logfile_path = os.path.abspath(os.path.join(config_dir, logfile_path + f".{LOG_FILE_TYPE}"))

DISABLED_LOGGERS = config("DISABLED_LOGGERS", cast=Csv(), default='')
"""Loggers that will be excluded on all outputs
"""

DISABLED_LOGGERS += ['daphne.http_protocol', 'daphne.server', 'daphne.ws_protocol', 'django.channels.server',
                     'asyncio', 'openai', "urllib3", "matplotlib", "sentence_transformers.SentenceTransformer"]
disabled_logger_conf = {i: {'level': 'WARNING'} for i in DISABLED_LOGGERS}

LOG_FMT = config("LOG_FMT",
                 default="%(levelname)s '%(message)s' -%(asctime)s-%(name)s-(File \"%(pathname)s\", line %(lineno)d)")
"""Format to be used for logging. See https://docs.python.org/3/library/logging.html#logrecord-attributes
There is an additional session_id attribute. It's behaviour is defined by LOG_UID_MODE
"""

LOG_UID_MODE = config("LOG_UID_MODE", default="username", cast=Choices(["none", "session", "username"]))
"""Either none, session or username. None means attribute will stay empty. session means filling with session identifier.
username with username.
"""

CONSOLE_USE_COLORS = config("CONSOLE_USE_COLORS", default =True, cast=bool)
"""Wether to print in colors to console. On some systems that isn't supported in which case you will get flooded
with control sequences. Use this to deactivate colors in the console.
"""

MAX_LOG_SIZE = config("MAX_LOG_SIZE", default=16, cast=int)
"""Max file size in kb before new logfile will be created. Normally there are 2 backup logfiles.
1 kb~6-9 log messages for txt and ~4-7 for html
"""
logging.setLoggerClass(plugins.log_helper.RIXALogger)

LOG_TIME_FMT = config("LOG_TIME_FMT",default="%a %H:%M:%S")
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'RIXAConsole': {
            '()': 'plugins.log_helper.RIXAFormatter',
            "colormode": "console" if CONSOLE_USE_COLORS else "none",
            "fmt_string": LOG_FMT,
            "time_fmt": LOG_TIME_FMT
        },

        'RIXAFile': {
            '()': 'plugins.log_helper.RIXAFormatter',
            "colormode": LOG_FILE_TYPE,
            "fmt_string": LOG_FMT,
            "time_fmt": LOG_TIME_FMT
        }
    },
    'filters': {
        'RIXAFilter': {
            '()': 'plugins.log_helper.RIXAFilter',
            "uid_mode": LOG_UID_MODE
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'filters': ['RIXAFilter'],
            'class': 'logging.StreamHandler',
            'formatter': 'RIXAConsole'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': MAX_LOG_SIZE * 1024,
            'backupCount': 2,
            'filename': logfile_path,
            'level': 'DEBUG',
            'filters': ['RIXAFilter'],
            'formatter': 'RIXAFile',
        } if LOG_FILE_TYPE != "none" else {'class': "logging.NullHandler"}
    },
    'loggers': {
        'root': {
            'handlers': ['console', 'file'] if LOG_FILE_TYPE != "none" else ["console"],
            'level': config("ROOT_LOG_LEVEL", default = "INFO"),
            'class': "plugins.log_helper.RIXALogger"
        },
    }
}

LOGGING['loggers'].update(disabled_logger_conf)

# import logging.config
# logging.config.dictConfig(LOGGING)
# logging.setLoggerClass(plugins.log_helper.RIXALogger)
# plugins.log_helper.RIXALogger.


PYENV_LOC = config("MANAGED_VENVS", default=False, cast=bool)
"""If set to an existing path with pyenv in it you allow the server to manage venvs on its own. 
"""

PYENV_PY_BASE = config("PYENV_PY_BASE", default = "3.11")
"""Standard python version to use for managed venvs unless otherwise specified.
"""

# stack_print_level = StackPrint.FULL
"""Set output level for giving stack and exception when parsing plugins
"""

GENERATE_INTERMEDIARY_FILES = config("GENERATE_INTERMEDIARY_FILES", default=False, cast=bool)
"""Wether or not to dump all sorts of stuff into a new debug folder in the working dir.
Only really useful for development on the plugin system itself.
"""

if GENERATE_INTERMEDIARY_FILES:
    DEBUG_PATH = os.path.join(config_dir, "debug")
    if not os.path.exists(DEBUG_PATH):
        os.mkdir(DEBUG_PATH)

additional_search_paths = [os.path.abspath(os.path.join(config_dir, i)) if i[0] != "/" else i
                           for i in config("PLUGIN_PATHS", cast=Csv())]
PLUGIN_PATHS = [os.path.abspath(os.path.join(__file__, "../..", "plugins/StandardPlugins"))] + additional_search_paths
"""Where to search for plugins besides the current working directory
"""

SHOW_ALL_PLUGIN_EXCEPTIONS = config("SHOW_ALL_PLUGIN_EXCEPTIONS", default=False, cast=bool)
"""If set to false exceptions occuring in plugins will vanish. Otherwise they are formatted and logged on the debug level.
"""

NLP_BACKEND = config("NLP_BACKEND", default="none")
"""Which NLP backend to use. If the specified backend has not been loaded it will reset to none.
None means the chat only supports manual commands.
"""

NLP_GREETING = config("NLP_GREETING", default="Hey there. I am PIXI and there for all questions you may have.")
"""Greeting message when user connects to server
"""

MAX_BLOCKING_CALLS = config("MAX_BLOCKING_CALLS", cast=int, default=10)
"""Max number of concurrent sync awaitables. Corresponds to the maximum number of non local plugin calls the server
handles in total.
"""

MAX_USER_JOBS = config("MAX_USER_JOBS", cast=int, default=2)
"""Max non async jobs that a connected user can commit
"""

MAX_PLUGIN_STACK_DEPTH = config("MAX_PLUGIN_STACK_DEPTH", cast=int, default=5)
"""Basically the maximum depth of nested function calls between plugins. Prevents circular deadlock.
"""
EXCLUDED_PLUGINS = config("EXCLUDED_PLUGINS", cast=Csv(), default="debug_remote, debug, plot")

MAX_LOAD_TIME_PER_MODULE = config("MAX_LOAD_TIME_PER_MODULE", default = 100, cast=int)
"""Multiplied by 0.01s. You can change this to prevent a plugin timing out while loading a huge module. On the flipside
it will take longer for the server to skip crashed plugins.
"""

IGNORE_PLUGIN_WARNINGS =config("IGNORE_PLUGIN_WARNINGS", default = True, cast=bool)
"""Disable this if you suspect faulty behaviour could be missing due to a missing warning. Will add some annoying mesages.
"""

DISABLE_PLUGIN_MODULE_CHECK = config("DISABLE_PLUGIN_MODULE_CHECK", default = False, cast=bool)
"""If activated the server will not check if a specified venv and plugin are compatible. Can be useful if you import via adding paths
or use a more complicated setup for imports.
Be aware that should you have missing imports and this activated the server will be in a unsafe state.
"""

DEFAULT_PLUGIN_VENV = config("DEFAULT_PLUGIN_VENV", default=None)

DISABLE_CHAT = config("DISABLE_CHAT", default=False, cast=bool)

REQUIRE_LOGIN_CHAT = config("REQUIRE_LOGIN_CHAT", default =False, cast=bool)

WEBSITE_TITLE = config("WEBSITE_TITLE", default="Home")
CHAT_TITLE = config("CHAT_TITLE", default="XAI Buddy")
ALWAYS_MAXIMIZE_CHAT = config("ALWAYS_MAXIMIZE_CHAT", default=False, cast=bool)


INTERCEPT_CHAT = config("INTERCEPT_CHAT", default=False, cast=bool)

ALL_SETTINGS = config.repository.data
