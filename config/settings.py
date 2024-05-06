from pathlib import Path
from urllib.parse import urlparse
from django.utils import timezone
import os
from django.contrib.messages import constants as messages
import logging, copy
from django.utils.log import DEFAULT_LOGGING
from environ import Env

# custom logging filter to suppress certain errors (such as Forbidden and Not Found)

LOGGING = copy.deepcopy(DEFAULT_LOGGING)
LOGGING['filters']['suppress_errors'] = {
    '()': 'config.settings.SuppressErrors'  
}
LOGGING['handlers']['console']['filters'].append('suppress_errors')

class SuppressErrors(logging.Filter):
    def filter(self, record):
        WARNINGS_TO_SUPPRESS = [
            'Forbidden',
            'Not Found'
        ]
        # Return false to suppress message.
        return not any([warn in record.getMessage() for warn in WARNINGS_TO_SUPPRESS])

#logging.basicConfig(level=logging.DEBUG)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-2y0@hfzu761goc9!m&!#if&(vhcg=!uzre027l48r&oh_c^xcx'

# recommended by https://cloud.google.com/python/django/appengine
env = Env(
    DEBUG=(bool, False),
    PROD=(bool, False),
    DEMO=(bool, False),
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

PROD = env('PROD')

DEMO = env('DEMO')

# https://cloud.google.com/python/django/appengine
# for deployment

if PROD:
    APPENGINE_URL = env("APPENGINE_URL", default=None)
    if APPENGINE_URL:
        # Ensure a scheme is present in the URL before it's processed.
        if not urlparse(APPENGINE_URL).scheme:
            APPENGINE_URL = f"https://{APPENGINE_URL}"

        ALLOWED_HOSTS = [urlparse(APPENGINE_URL).netloc]
        CSRF_TRUSTED_ORIGINS = [APPENGINE_URL]
        SECURE_SSL_REDIRECT = True
    else:
        ALLOWED_HOSTS = ["*"]
else:
    ALLOWED_HOSTS = ["*"]

INTERNAL_IPS = [
    "127.0.0.1",
]

# Application definition

INSTALLED_APPS = [
    'competitions.apps.CompetitionsConfig', 
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'hijack',
    'hijack.contrib.admin',
    'debug_toolbar',
    'crispy_forms',
    'crispy_bootstrap5',
    'mathfilters', # pip install django-mathfilters
    'whitenoise.runserver_nostatic',
    'simple_history',
    'social_django',
    #'colorfield', # pip install django-colorfield
    #'easy_timezones', # pip install django-easy-timezones
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'hijack.middleware.HijackUserMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
    'config.custom.middleware.TimezoneMiddleware', # custom
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        "DIRS": [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
                'config.custom.context_processors.tz', # custom context processor: passes in current timezone as "TIME_ZONE"
                'config.custom.context_processors.user', # custom context processor: passes in user as variable "user"
                'config.custom.context_processors.current_time', # custom context processor: passes in variables "NOW", "CURRENT_TIME", "CURRENT_DATE"
            ],
        },
    },
]

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

WSGI_APPLICATION = 'config.wsgi.application'

AUTHENTICATION_BACKENDS = [
    'social_core.backends.google.GoogleOpenId',
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.google.GoogleOAuth',
    'django.contrib.auth.backends.ModelBackend',
]

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

if PROD:
    DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': '<name>',
        'USER': '<db_username>',
        'PASSWORD': '<password>',
        'HOST': '<db_hostname_or_ip>',
        'PORT': '<db_port>',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

LANGUAGES = [
    ('en', 'English'),
    ('es', 'Spanish'),
    ('fr', 'French'),
]

LOCALE_PATHS = [os.path.join(BASE_DIR, 'locale')]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"

CRISPY_TEMPLATE_PACK = "bootstrap5"

STATIC_URL = f"/static/"

if DEBUG:
    # this only applies if debug=true
    STATICFILES_DIRS = [
        os.path.join(BASE_DIR, 'static'),
    ]
else:
    # this is what whitenoise uses (for prod)
    STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / '/uploads/'

# for message framework
# the django red alert class is called "danger", django calls it "error"
# this changes it so it uses danger (for the bootstrap class)
MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}

SHOW_TOOLBAR_CALLBACK = lambda request: DEBUG

LOGIN_REDIRECT_URL = '/'

LOGIN_URL = '/accounts/login/'
