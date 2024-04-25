import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SECRET_KEY = 'your-secret-key'
DB_ENCRYPTION_KEY = '/etc/pulp/certs/database_fields.symmetric.key'
DEBUG = True
DOMAIN_ENABLED = True

# Pulp-specific settings
ALLOWED_CONTENT_CHECKSUMS = ['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512']
CONTENT_PATH_PREFIX = '/pulp/content/'
CONTENT_APP_TTL = 30
REMOTE_USER_ENVIRON_NAME = 'REMOTE_USER'
FILE_UPLOAD_TEMP_DIR = '/var/lib/pulp/tmp/'
WORKING_DIRECTORY = '/var/lib/pulp/tmp/'
MEDIA_ROOT = '/var/lib/pulp/'
DEFAULT_FILE_STORAGE = 'pulpcore.app.models.storage.FileSystem'
HIDE_GUARDED_DISTRIBUTIONS = False
REDIRECT_TO_OBJECT_STORAGE = False


ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    "django_filters",
    "django_guid",
    "drf_spectacular",
    "import_export",
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    "django.contrib.postgres",
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'pulpcore.app',
    'pulp_r.app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'pulp_r.app.urls'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

STATIC_URL = '/static/'

# Redis configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_PASSWORD = ''
# Redis settings
REDIS_URL = f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}'
WORKING_DIRECTORY = '/var/lib/pulp/tmp/'

# Celery settings
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_WORKER_CONCURRENCY = 4
CELERY_TASK_ROUTES = {
    'pulpcore.app.tasks.base.general_update': {'queue': 'reserved_resource_worker_1'},
    'pulpcore.app.tasks.base.general_delete': {'queue': 'reserved_resource_worker_1'},
}
CONTENT_ORIGIN = 'http://localhost:24817'
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'pulpcore': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'pulp_r.app': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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