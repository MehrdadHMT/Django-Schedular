"""Common settings and globals."""

from datetime import timedelta
import os
from os.path import abspath, dirname, join, normpath
from sys import path
from socket import gethostbyname_ex, gethostname
from django_redis import get_redis_connection
from corsheaders.defaults import default_headers

########## PATH CONFIGURATION
# Absolute filesystem path to the Django project directory:
DJANGO_ROOT = dirname(abspath(__file__))

# Absolute filesystem path to the top-level project folder:
SITE_ROOT = dirname(DJANGO_ROOT)

# Site name:
SITE_NAME = os.getenv('SITE_NAME', 'project')

# Add our project to our pythonpath, this way we don't need to type our project
# name in our dotted import paths:
path.append(DJANGO_ROOT)
########## END PATH CONFIGURATION


########## DEBUG CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = os.getenv('DEBUG', 'false') == 'true'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#template-debug
TEMPLATE_DEBUG = DEBUG

TEST_RUNNER = 'django.test.runner.DiscoverRunner'
########## END DEBUG CONFIGURATION


########## MANAGER CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = (
    ('Mehrdad Bagheri', 'Mehrdad.HMT@gmail.com'),
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS
########## END MANAGER CONFIGURATION


########## DATABASE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': os.getenv('DATABASE_ENGINE', 'django_db_geventpool.backends.postgresql_psycopg2'),
        'NAME': os.getenv('DATABASE_NAME', 'db'),
        'USER': os.getenv('DATABASE_USER', 'user'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'password'),
        'HOST': os.getenv('DATABASE_SERVICE_HOST', 'database'),
        'PORT': os.getenv('DATABASE_SERVICE_PORT', 5432),
        'CONN_MAX_AGE': int(os.getenv('CONN_MAX_AGE', 0)),
        'OPTIONS': {
            'MAX_CONNS': int(os.getenv('DB_POOL_MAX_CONNS', '1000')),
            'REUSE_CONNS': int(os.getenv('DB_POOL_REUSE_CONNS', '10'))
        }
    }
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv('REDIS_SERVICE_HOST', 'redis'),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "MAX_ENTRIES": 1000,
            "PASSWORD": os.getenv('REDIS_PASSWORD', ''),
        },
        "KEY_PREFIX": "Nilva"
    }
}
########## END DATABASE CONFIGURATION


########## GENERAL CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#time-zone
TIME_ZONE = 'Asia/Tehran'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGES = (
    ('en', 'English'),
    ('fa', 'Persian'),
)
LOCALE_PATHS = (
    os.path.join(DJANGO_ROOT, 'locale/'),
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True
########## END GENERAL CONFIGURATION


########## MEDIA CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = normpath(join(DJANGO_ROOT, 'media'))

# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = '/media/'
########## END MEDIA CONFIGURATION


########## STATIC FILE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = normpath(join(SITE_ROOT, 'staticfiles'))

# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = '/static/'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = (
    # normpath(join(DJANGO_ROOT, '../client/dist')),
)

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)
########## END STATIC FILE CONFIGURATION


########## SECRET CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = os.getenv('SECRET_KEY', '8lu*6g0lg)9z!ba+a$ehk)xt)x%rxgb$i1&amp;022shmi1jcgihb*')
STATIC_AUTH_KEY = os.getenv('STATIC_AUTH_KEY', 'rN4AYQ9a5rw2nu')
########## END SECRET CONFIGURATION

########## TEMPLATE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # insert your TEMPLATE_DIRS here
            '/django/project/templates'
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.static',
                'django.template.context_processors.media',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
########## END TEMPLATE CONFIGURATION


########## MIDDLEWARE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#middleware-classes
MIDDLEWARE = (
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'middleware.ResponseLogMiddleware',
    'middleware.ResponseHeaderMiddleware',
    'middleware.HealthCheckMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
)
########## END MIDDLEWARE CONFIGURATION


########## URL CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#root-urlconf
ROOT_URLCONF = '%s.urls' % SITE_NAME
########## END URL CONFIGURATION


########## APP CONFIGURATION
DJANGO_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
)

THIRD_PARTY_APPS = (

    # REST
    'rest_framework',

    # CORS
    'corsheaders',

    # Swagger
    'drf_spectacular',
    'drf_spectacular_sidecar',

    # metric tools
    'django_prometheus',

    # debug tool
    'debug_toolbar',

)

LOCAL_APPS = (
    'apps.tasks.apps.MyAppConfig',
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS
########## END APP CONFIGURATION

########## REST FRAMEWORK CONFIGURATION

SPECTACULAR_SETTINGS = {
    'TITLE': 'Task Scheduler RestApi',
    'DESCRIPTION': 'Task Scheduler Restapi project',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_SETTINGS': {
        'displayRequestDuration': True,
    },
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
}

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DATETIME_FORMAT': '%s.%f',
    'DEFAULT_SCHEMA_CLASS': 'project.swagger_default_schema.CustomAutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'DEFAULT_METADATA_CLASS': None,
    'PAGE_SIZE': 10
}
########## END REST FRAMEWORK CONFIGURATION


########## LOGGING CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        "json": {
            '()': 'json_log.TaskSchedulerJsonFormatter',
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/django/django.log',
            'formatter': 'json',
        },
        'file_requests': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/django/requests.log',
            'formatter': 'json',
        },
        'file_providers': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/django/providers.log',
            'formatter': 'json',
        },
        'file_jobs': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/django/jobs.log',
            'formatter': 'json',
        },
    },
    'loggers': {
        '': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'provider_logger': {
            'handlers': ['file_providers'],
            'level': 'INFO',
            'propagate': False,
        },
        'requests_logger': {
            'handlers': ['file_requests', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'jobs_logger': {
            'handlers': ['file_jobs'],
            'level': 'INFO',
            'propagate': False,
        }
    }
}
########## END LOGGING CONFIGURATION

########## CORS
# If this is used then `CORS_ORIGIN_WHITELIST` will not have any effect
CORS_ORIGIN_ALLOW_ALL = os.getenv('CORS_ORIGIN_ALLOW_ALL', 'false') == 'true'
CORS_ALLOW_CREDENTIALS = os.getenv('CORS_ALLOW_CREDENTIALS', 'false') == 'true'

CORS_ORIGIN_WHITELIST = os.getenv("CORS_ORIGIN_WHITELIST", "http://localhost:7000").split(";")
CORS_ORIGIN_REGEX_WHITELIST = os.getenv("CORS_ORIGIN_REGEX_WHITELIST", "^http:\/\/192\.168\.\d+\.\d+:\d+$").split(";")

CORS_ALLOW_HEADERS = list(default_headers) + os.getenv('CORS_ALLOW_HEADERS', 'user-device').split(';')

if DEBUG:
    hostname, _, ips = gethostbyname_ex(gethostname())
    INTERNAL_IPS = [ip[: ip.rfind(".")] + ".1" for ip in ips] + ["127.0.0.1", "10.0.2.2", "localhost", "0.0.0.0"]
########## END CORS CONFIGURATION


########## WSGI CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = 'wsgi.application'
########## END WSGI CONFIGURATION

# AUTH_USER_MODEL = 'tasks.User'

ALLOWED_HOSTS = [gethostname(), ] + list(set(gethostbyname_ex(gethostname())[2])) + os.getenv('ALLOWED_HOSTS', 'localhost;0.0.0.0;restapi').split(';')

# Setup support for proxy headers
SECURE_HSTS_SECONDS = 31536000
USE_X_FORWARDED_HOST = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Sentry
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    integrations=[DjangoIntegration()]
)

# values
VALUES = {
    200: "SUCCESS",
    204: "NO CONTENT",
    207: "MULTI-STATUS",
    208: "ALREADY REPORTED",
    302: "302 FOUND",
    400: "BAD REQUEST",
    401: "Unauthorized",
    403: "FORBIDDEN",
    404: "NOT FOUND",
    406: "NOT ACCEPTABLE",
    409: "CONFLICT",
    413: "PAYLOAD TOO LARGE",
    423: "LOCKED",
    422: "UNPROCESSABLE ENTITY",
    500: "INTERNAL SERVER ERROR",
    503: "SERVICE UNAVAILABLE",
    "DEFAULT_STATUSES_ANY": {400: "BAD REQUEST"},
    "DEFAULT_STATUSES_AUTH": {401: "Unauthorized"},

    "USER_FORWARDED_IP": os.getenv("USER_FORWARDED_IP", 'X-Forwarded-For'),
    "HEADER_ORIGINAL_URI": os.getenv("HEADER_ORIGINAL_URI", 'X-Original-URI'),

    # Kafka vars
    "KAFKA_BOOTSTRAP_SERVER": os.getenv('KAFKA_BOOTSTRAP_SERVER', 'kafka:9092').split(','),

    # Metrics
    "IS_ENABLE_METRICS": os.getenv('ENABLE_METRICS', 'false') == 'true',
    "METRICS_EXPORT_PORT": int(os.getenv("METRICS_EXPORT_PORT", 8001)),
    "EXCEPTION_METRICS_PREFIX": os.getenv('EXCEPTION_METRICS_PREFIX', 'exception-metrics-prefix'),
    "EXCEPTION_METRICS_TTL": os.getenv('EXCEPTION_METRICS_TTL', 5 * 60),
    "PING_INTERNET_SERVER_TIMEOUT": int(os.getenv('PING_INTERNET_SERVER_TIMEOUT', 3)),
    "CHECK_INTERNET_HOST": os.getenv('CHECK_INTERNET_HOST', 'google.com'),

    "HEADER_LOGGER_ENABLE": os.getenv('HEADER_LOGGER_ENABLE', "false") == "true",
    "MAX_WORKERS": int(os.getenv('MAX_WORKERS', 8)),
    "TIME_OUT": int(os.getenv('TIME_OUT', 900)),
}

# Prometheus config
if VALUES['IS_ENABLE_METRICS']:
    PROMETHEUS_METRICS_EXPORT_PORT_RANGE = range(VALUES['METRICS_EXPORT_PORT'], VALUES['METRICS_EXPORT_PORT'] + 1)
    PROMETHEUS_EXPORT_MIGRATIONS = False

# Redis Connection
REDIS_CONNECTION = get_redis_connection('default')
