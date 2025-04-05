import logging
from pathlib import Path
from django.utils.translation import gettext_lazy as _

import os
from decouple import Config, RepositoryEnv, Csv, Choices
from warnings import warn


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
# DEBUG = config("DEBUG", default=True, cast=bool)

"""SECURITY WARNING: don't run with debug turned on in production!
"""
MAINTENANCE_MODE = config("MAINTENANCE_MODE", default=True, cast=bool)
"""prevents access to server outside of localhost. With asgi blocks all connections.
"""

ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())
"""List of domains which the webserver serves. '*' means all connections will be accepted.
Needs to be properly configured before deploying.
"""


PRIMARY_URL = config("PRIMARY_URL", default="localhost:8000")

STATISTICS_COLLECTION_INTERVAL = config("STATISTICS_COLLECTION_INTERVAL", default=10, cast=int)
"""Interval in seconds in which the server collects statistics about user activity."""
KNOWLEDGE_DB_LOC = config("KNOWLEDGE_DB_LOC", default=None, cast=str)
# do not touch
INSTALLED_APPS = [
    'daphne',
    'account_managment.apps.AccountManagmentConfig',
    'dashboard.apps.DashboardConfig',
    'management.apps.ManagementConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "bootstrap5"
    # 'rosetta',

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'account_managment.visit_statistics.SimpleMiddleware'

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
        'NAME': config("DB_NAME", default=os.path.join(config_dir, 'db.sqlite3'))
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

SITE_ROOT = BASE_DIR
STATICFILES_DIRS = (
    os.path.join(SITE_ROOT, 'static/'),
)

# STATIC_ROOT = config("STATIC_ROOT", default = None)
STATIC_ROOT = config("STATIC_ROOT", default="./staticfiles")
# STATIC_ROOT = (os.path.join(BASE_DIR, 'static_files/'))
STATIC_URL = '/static/'
# STATICFILES_DIRS = [
#     BASE_DIR / "static",
#     BASE_DIR / "dashboard/static",
# ]


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

CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", cast=Csv(), default="")

ROSETTA_SHOW_AT_ADMIN_PANEL = True
ROSETTA_EXCLUDED_APPLICATIONS = ('django.contrib.admin')

SESSION_EXPIRE_AT_BROWSER_CLOSE = config("SESSION_EXPIRE_AT_BROWSER_CLOSE", default=False, cast=bool)
SESSION_COOKIE_AGE = config("SESSION_COOKIE_AGE", default=60 * 60 * 24 * 14, cast=int)
"""Time in seconds before session is marked as invalid
"""

AUTH_USER_MODEL = 'account_managment.User'

LOGIN_URL = "account_user_login"

NUM_SERVER_WORKER_THREADS = config("NUM_WORKER_THREADS", default=4, cast=int)

PATCH_USER_MODEL = config("PATCH_USER_MODEL", default=False, cast=bool)
"""Patch users that have been created via the admin interface or other means."""

from rixaplugin.settings import *

PYENV_LOC = config("MANAGED_VENVS", default=False, cast=bool)
"""If set to an existing path with pyenv in it you allow the server to manage venvs on its own. 
"""

PYENV_PY_BASE = config("PYENV_PY_BASE", default="3.11")
"""Standard python version to use for managed venvs unless otherwise specified.
"""

# stack_print_level = StackPrint.FULL
"""Set output level for giving stack and exception when parsing plugins
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

MAX_LOAD_TIME_PER_MODULE = config("MAX_LOAD_TIME_PER_MODULE", default=100, cast=int)
"""Multiplied by 0.01s. You can change this to prevent a plugin timing out while loading a huge module. On the flipside
it will take longer for the server to skip crashed plugins.
"""

IGNORE_PLUGIN_WARNINGS = config("IGNORE_PLUGIN_WARNINGS", default=True, cast=bool)
"""Disable this if you suspect faulty behaviour could be missing due to a missing warning. Will add some annoying mesages.
"""

DISABLE_PLUGIN_MODULE_CHECK = config("DISABLE_PLUGIN_MODULE_CHECK", default=False, cast=bool)
"""If activated the server will not check if a specified venv and plugin are compatible. Can be useful if you import via adding paths
or use a more complicated setup for imports.
Be aware that should you have missing imports and this activated the server will be in a unsafe state.
"""

DEFAULT_PLUGIN_VENV = config("DEFAULT_PLUGIN_VENV", default=None)

DISABLE_CHAT = config("DISABLE_CHAT", default=False, cast=bool)

# REQUIRE_LOGIN_CHAT = config("REQUIRE_LOGIN_CHAT", default=False, cast=bool)
# delete when no errors are found

DEFAULT_BACKGROUND_MESSAGE = "## Welcome"

ENABLE_RAG_MANAGEMENT_SITES = config("ENABLE_RAG_MANAGEMENT_SITES", default=False, cast=bool)

WEBSITE_TITLE = config("WEBSITE_TITLE", default="Home")
CHAT_TITLE = config("CHAT_TITLE", default="XAI Buddy")
ALWAYS_MAXIMIZE_CHAT = config("ALWAYS_MAXIMIZE_CHAT", default=False, cast=bool)


# INTERCEPT_CHAT = config("INTERCEPT_CHAT", default=False, cast=bool)
# delete when no errors are found

ENABLE_CHAT_TELEMETRY = config("ENABLE_CHAT_TELEMETRY", cast=bool, default=True)
"""Write telemetry into chat histories
"""
ENABLE_TAB_SWITCH_TELEMETRY = config("ENABLE_TAB_SWITCH_TELEMETRY", cast=bool, default=False)
"""Log additionally tab switches by user/defocussing of window.
Use only for small user sizes as this adds a huge amount of data.
"""

ENABLE_ONBOARDING = config("ENABLE_ONBOARDING", cast=bool, default=True)
"""Show onboarding defined in static/assets/onboarding.json
"""
HIDE_SETTINGS = config("HIDE_SETTINGS", default=False, cast=bool)
"""Whether or not to show settings in standard UI. Does not block websocket requests to change settings"""

USERSTUDY = config("USERSTUDY", default="", cast=str)
"""DO NOT USE! Activates various hardcoded segments for userstudies
"xai1" for dashboard/chat/chatdashboard comparison
"innovation" for RAG study"""

ALL_SETTINGS = config.repository.data
