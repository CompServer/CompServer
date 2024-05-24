import copy
import io
import logging
import os
from pathlib import Path
from urllib.parse import urlparse

from django.contrib.messages import constants as messages
from django.utils.log import DEFAULT_LOGGING
import environ
import yaml

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

# [START cloudrun_django_secret_config]
# SECURITY WARNING: don't run with debug turned on in production!
# Change this to "False" when you are ready for production
env = environ.Env(DEBUG=(bool, True))
env_file = os.path.join(BASE_DIR, ".env")


PROD = env("PROD", default=False)

if PROD:
    # don't need these imports unless prod is true
    # can skip some reqs if prod isn't on
    # because it's only needed for secret manager, seperate requirements file
    import google.auth
    from google.cloud import secretmanager
    # Attempt to load the Project ID into the environment, safely failing on error.
    try:
        _, os.environ["GOOGLE_CLOUD_PROJECT"] = google.auth.default() # type: ignore
    except google.auth.exceptions.DefaultCredentialsError:
        pass

    if os.path.isfile(env_file):
        # Use a local secret file, if provided

        env.read_env(env_file)
    # [START_EXCLUDE]
    elif os.getenv("TRAMPOLINE_CI", None):
        # Create local settings if running with CI, for unit testing

        placeholder = (
            f"SECRET_KEY=a\n"
            "GS_BUCKET_NAME=None\n"
            f"DATABASE_URL=sqlite://{os.path.join(BASE_DIR, 'db.sqlite3')}"
        )
        env.read_env(io.StringIO(placeholder))
    # [END_EXCLUDE]
    elif os.environ.get("GOOGLE_CLOUD_PROJECT", None):
        # Pull secrets from Secret Manager
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")

        client = secretmanager.SecretManagerServiceClient()
        settings_name = os.environ.get("SETTINGS_NAME", "django_settings")
        name = f"projects/{project_id}/secrets/{settings_name}/versions/latest"
        payload = client.access_secret_version(name=name).payload.data.decode("UTF-8")

        env.read_env(io.StringIO(payload))
    else:
        raise Exception("No local .env or GOOGLE_CLOUD_PROJECT detected. No secrets found.")
    SECRET_KEY = env("SECRET_KEY")
    SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = env('GOOGLE_CLIENT_ID')
    SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = env('GOOGLE_CLIENT_SECRET')
    SOCIAL_AUTH_GITHUB_KEY = env('GITHUB_CLIENT_ID')
    SOCIAL_AUTH_GITHUB_SECRET = env('GITHUB_CLIENT_SECRET')
else:
    if os.path.exists('secrets.yml'):
        with open('secrets.yml') as f:
            config = dict(yaml.safe_load(f))
            SECRET_KEY = config["SECRET_KEY"]
            SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = config['GOOGLE_CLIENT_ID']
            SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = config['GOOGLE_CLIENT_SECRET']
            SOCIAL_AUTH_GITHUB_KEY = config['GITHUB_CLIENT_ID']
            SOCIAL_AUTH_GITHUB_SECRET = config['GITHUB_CLIENT_SECRET']
    else:
        raise Exception("No local .env or secrets.yml detected. No secrets found.")

assert SECRET_KEY is not None
    #recommended by https://cloud.google.com/python/django/appengine
#     env = Env(
#         DEBUG=(bool, False),
#         PROD=(bool, False),
#         DEMO=(bool, False),
#   )

DEBUG = env("DEBUG", default=False)

DEMO = env('DEMO', default=False)


# https://cloud.google.com/python/django/appengine
# for deployment

# if PROD:
#     APPENGINE_URL = env("APPENGINE_URL", default=None)
#     if APPENGINE_URL:
#         # Ensure a scheme is present in the URL before it's processed.
#         if not urlparse(APPENGINE_URL).scheme:
#             APPENGINE_URL = f"https://{APPENGINE_URL}"

#         ALLOWED_HOSTS = [urlparse(APPENGINE_URL).netloc]
#         CSRF_TRUSTED_ORIGINS = [APPENGINE_URL]
#         SECURE_SSL_REDIRECT = True
#     else:
#         ALLOWED_HOSTS = ["*"]
# else:
#     ALLOWED_HOSTS = ["*"]

# INTERNAL_IPS = [
#     "127.0.0.1",
# ]

# [START cloudrun_django_csrf]
# SECURITY WARNING: It's recommended that you use this when
# running in production. The URL will be known once you first deploy
# to Cloud Run. This code takes the URL and converts it to both these settings formats.
if PROD:
    CLOUDRUN_SERVICE_URL = env("CLOUDRUN_SERVICE_URL", default=None)
    if CLOUDRUN_SERVICE_URL:
        ALLOWED_HOSTS = [urlparse(CLOUDRUN_SERVICE_URL).netloc]
        CSRF_TRUSTED_ORIGINS = [CLOUDRUN_SERVICE_URL]
        SECURE_SSL_REDIRECT = True
        SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    else:
        ALLOWED_HOSTS = ["*"]
else:
    ALLOWED_HOSTS = ["*"]

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
    'compressor',
    'sass_processor',
    'simple_history',
    'social_django',
    'template_partials',
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
                'config.custom.context_processors.settings_values', # custom context processor: passes settings of interest from settings.py (currently just DEMO)
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
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.google.GoogleOAuth',
    'django.contrib.auth.backends.ModelBackend',
]

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# if PROD:
#     DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         'NAME': '<name>',
#         'USER': '<db_username>',
#         'PASSWORD': '<password>',
#         'HOST': '<db_hostname_or_ip>',
#         'PORT': '<db_port>',
#         }
#     }
# else:
#     DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.sqlite3',
#             'NAME': BASE_DIR / 'db.sqlite3',
#         }
#   }

if PROD:
    DATABASES = {"default": env.db()}

    if os.getenv("USE_CLOUD_SQL_AUTH_PROXY", None):
        DATABASES["default"]["HOST"] = "127.0.0.1"
        DATABASES["default"]["PORT"] = 5432
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
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
    COMPRESS_ROOT = STATICFILES_DIRS[0]
    SASS_PROCESSOR_ROOT = STATICFILES_DIRS[0]
    # comment out the above and uncomment the below when collecting static
    #STATIC_ROOT = os.path.join(BASE_DIR, 'static')
else:
    # this is what whitenoise uses (for prod)
    STATIC_ROOT = os.path.join(BASE_DIR, 'static')
    SASS_PROCESSOR_ROOT = STATIC_ROOT

MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / '/uploads/'

STATICFILES_FINDERS = [
    'compressor.finders.CompressorFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'sass_processor.finders.CssFinder',
]

# COMPRESS_PRECOMPILERS = [
#         ('text/x-scss', 'django_libsass.SassCompiler'),
# ]

COMPRESS_PRECOMPILERS = ( 
    ('text/x-scss', 'sass {infile} {outfile}'), 
)


GS_DEFAULT_ACL = "publicRead"

# for message framework
# the django red alert class is called "danger", django calls it "error"
# this changes it so it uses danger (for the bootstrap class)
MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}

SHOW_TOOLBAR_CALLBACK = lambda request: DEBUG

LOGIN_REDIRECT_URL = '/'

LOGIN_URL = '/accounts/login/'

# SOCIAL_AUTH_GOOGLE_OAUTH_KEY = ''
# SOCIAL_AUTH_GOOGLE_OAUTH_SECRET = ''
SOCIAL_AUTH_URL_NAMESPACE = 'social'
SOCIAL_AUTH_JSONFIELD_ENABLED = True
SOCIAL_AUTH_REDIRECT_IS_HTTPS = True

X_FRAME_OPTIONS = 'SAMEORIGIN'

# insert urls here
CSRF_TRUSTED_ORIGINS = [
    'https://compserver.ucls.uchicago.edu',
    'https://compserver-service-hoxlb46hdq-uc.a.run.app'
]


AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    # 'social_core.backends.gitlab.GitLabOAuth2',
    'social_core.backends.google.GoogleOAuth2',
    #'rest_framework_social_oauth2.backends.DjangoOAuth2',
)


USE_SENTRY = True

if USE_SENTRY:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn="https://ecc96da365761b9276d136bcf2323a60@o4507297296023552.ingest.us.sentry.io/4507297296809984", # maybe we put this url in a secret?

        integrations=[
            DjangoIntegration()
        ],

        send_default_pii=True,

        environment='production' if PROD else 'development',

        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=1.0,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=1.0,
        enable_tracing=True,
    )

    # # add metrics to sentry
    # sentry_sdk.metrics.gauge(
    #     key="page_load",
    #     value=15.0,
    #     unit="millisecond",
    #     tags={
    #         "page": "/"
    #     }
    # )

    # # Add '15.0' to a distribution
    # # used for tracking the loading times of a component.
    # sentry_sdk.metrics.distribution(
    #     key="page_load",
    #     value=15.0,
    #     unit="millisecond",
    #     tags={
    #         "page": "/"
    #     }
    # )

