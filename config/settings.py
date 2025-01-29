import copy
import logging
import os
from pathlib import Path

from django.contrib.messages import constants as messages
from django.core.management.utils import get_random_secret_key
from django.utils.log import DEFAULT_LOGGING
import dj_database_url
# import environ
import yaml
# import git
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

# env = environ.Env(DEBUG=(bool, True))
# env_file = os.path.join(BASE_DIR, ".env")


PROD = os.getenv("PROD", "False") == "True"

if PROD:
    # # don't need these imports unless prod is true
    # # can skip some reqs if prod isn't on
    # # because it's only needed for secret manager, seperate requirements file
    # import google.auth
    # from google.cloud import secretmanager
    # # Attempt to load the Project ID into the environment, safely failing on error.
    # try:
    #     _, os.environ["GOOGLE_CLOUD_PROJECT"] = google.auth.default() # type: ignore
    # except google.auth.exceptions.DefaultCredentialsError:
    #     pass

    # if os.path.isfile(env_file):
    #     # Use a local secret file, if provided

    #     env.read_env(env_file)
    # # [START_EXCLUDE]
    # elif os.getenv("TRAMPOLINE_CI", None):
    #     # Create local settings if running with CI, for unit testing

    #     placeholder = (
    #         f"SECRET_KEY=a\n"
    #         "GS_BUCKET_NAME=None\n"
    #         f"DATABASE_URL=sqlite://{os.path.join(BASE_DIR, 'db.sqlite3')}"
    #     )
    #     env.read_env(io.StringIO(placeholder))
    # # [END_EXCLUDE]
    # elif os.environ.get("GOOGLE_CLOUD_PROJECT", None):
    #     # Pull secrets from Secret Manager
    #     project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")

    #     client = secretmanager.SecretManagerServiceClient()
    #     settings_name = os.environ.get("SETTINGS_NAME", "django_settings")
    #     name = f"projects/{project_id}/secrets/{settings_name}/versions/latest"
    #     payload = client.access_secret_version(name=name).payload.data.decode("UTF-8")

    #     env.read_env(io.StringIO(payload))
    # else:
    #     raise Exception("No local .env or GOOGLE_CLOUD_PROJECT detected. No secrets found.")
    SECRET_KEY = os.getenv("SECRET_KEY", get_random_secret_key())
    SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.getenv('GOOGLE_CLIENT_ID', default=None)
    SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', default=None)
    SOCIAL_AUTH_GITHUB_KEY = os.getenv('GITHUB_CLIENT_ID', default=None)
    SOCIAL_AUTH_GITHUB_SECRET = os.getenv('GITHUB_CLIENT_SECRET', default=None)
    SENTRY_URL = os.getenv('SENTRY_URL', default=None)
    SENTRY_REPLAY_URL = os.getenv('SENTRY_REPLAY_URL', default=None)
else:
    if os.path.exists('secrets.yml'):
        with open('secrets.yml') as f:
            config = dict(yaml.safe_load(f))
            SECRET_KEY = config["SECRET_KEY"]
            SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = config.get('GOOGLE_CLIENT_ID',None)
            SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = config.get('GOOGLE_CLIENT_SECRET',None)
            SOCIAL_AUTH_GITHUB_KEY = config.get('GITHUB_CLIENT_ID',None)
            SOCIAL_AUTH_GITHUB_SECRET = config.get('GITHUB_CLIENT_SECRET',None)
            SENTRY_URL = config.get('SENTRY_URL',None)
            SENTRY_REPLAY_URL = config.get("SENTRY_REPLAY_URL", None)
    else:
        # raise Exception("No local .env or secrets.yml detected. No secrets found.")
        SECRET_KEY = os.getenv("SECRET_KEY", get_random_secret_key())
        SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.getenv('GOOGLE_CLIENT_ID',None)
        SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.getenv('GOOGLE_CLIENT_SECRET',None)
        SOCIAL_AUTH_GITHUB_KEY = os.getenv('GITHUB_CLIENT_ID',None)
        SOCIAL_AUTH_GITHUB_SECRET = os.getenv('GITHUB_CLIENT_SECRET',None)
        SENTRY_URL = os.getenv('SENTRY_URL',None)
        SENTRY_REPLAY_URL = os.getenv("SENTRY_REPLAY_URL", None)


assert SECRET_KEY is not None
    #recommended by https://cloud.google.com/python/django/appengine
#     env = Env(
#         DEBUG=(bool, False),
#         PROD=(bool, False),
#         DEMO=(bool, False),
#   )

DEBUG = os.getenv("DEBUG", default="False").lower() == "true"

DEMO = os.getenv('DEMO', default="False").lower() == "true"

USE_SASS = os.getenv('USE_SASS', default="False").lower() == "true"

USE_SENTRY = os.getenv('USE_SENTRY', default="False").lower() == "true"

# https://stackoverflow.com/questions/31956506/get-short-sha-of-commit-with-gitpython
# try:
#     repo: git.Repo = git.Repo(search_parent_directories=True)
# except git.InvalidGitRepositoryError:
#     # this usually happens when performing a non running the app action (collectstatic, etc)

#     # also couldn't find a logger to use here, we can just print i guess
#     print("Warning: Could not find a git directory in the project. GitHub variables will be unset.")
#     repo = None

# if repo:
#     REMOTE_URL = repo.remote().url
#     if "github.com" in REMOTE_URL:
#         # Convert SSH URL to HTTPS if necessary
#         if REMOTE_URL.startswith("git@"):
#             REMOTE_URL = REMOTE_URL.replace("git@", "https://").replace(":", "/")

#         # Remove .git suffix if present
#         if REMOTE_URL.endswith(".git"):
#             REMOTE_URL = REMOTE_URL[:-4]

#     GITHUB_LATEST_COMMIT_SHORT = repo.git.rev_parse(repo.head.commit.hexsha, short=4)
#     GITHUB_LATEST_COMMIT = repo.git.rev_parse(repo.head.commit.hexsha)

#     tracking_branch = repo.head.reference.tracking_branch()
#     # Get the latest pushed commit hash for the current branch
#     if tracking_branch is not None:
#         GITHUB_LATEST_PUSHED_COMMIT_HASH = repo.git.rev_parse(f"{tracking_branch.name}")
#         GITHUB_LATEST_PUSHED_COMMIT_HASH_SHORT = GITHUB_LATEST_PUSHED_COMMIT_HASH[:5] # first 5 chars
#         GITHUB_LATEST_COMMIT_URL = f"{REMOTE_URL}/commit/{GITHUB_LATEST_PUSHED_COMMIT_HASH}"
#     else:
#         GITHUB_LATEST_PUSHED_COMMIT_HASH = None
#         GITHUB_LATEST_COMMIT_URL = None

#     if not tracking_branch:
#         tracking_branch = repo.active_branch

#     # tracking_branch.name usually gives something like "origin/branch", we remove the remote name and the slash by doing this 
#     GITHUB_CURRENT_BRANCH_NAME = tracking_branch.name.lstrip(f"{tracking_branch.remote_name}/")
#     GITHUB_CURRENT_BRANCH_URL = f"{REMOTE_URL}/tree/{GITHUB_CURRENT_BRANCH_NAME}"

#     # change this if you don't want people to see the github link/branch/commit
#     SHOW_GH_DEPLOYMENT_TO_ALL = False

#     # link to the version of github/gitlab that hosts the running version
#     GIT_URL = repo.remotes.origin.url
#     BRANCH = repo.active_branch

#     # sentry uses this RELEASE_VERSION variable to seperate errors, using the commit hash should help
#     # when tracing down issues
#     RELEASE_VERSION = GITHUB_LATEST_COMMIT
# else:
REMOTE_URL = None
GITHUB_LATEST_COMMIT_SHORT = None
GITHUB_LATEST_COMMIT = None
GITHUB_LATEST_PUSHED_COMMIT_HASH = None
GITHUB_LATEST_PUSHED_COMMIT_HASH_SHORT = None
GITHUB_LATEST_COMMIT_URL = None
GITHUB_CURRENT_BRANCH_NAME = None
GITHUB_CURRENT_BRANCH_URL = None
SHOW_GH_DEPLOYMENT_TO_ALL = None
GIT_URL = None
BRANCH = None
RELEASE_VERSION = None


# https://cloud.google.com/python/django/appengine
# for deployment

# if PROD:
#     APPENGINE_URL = os.getenv("APPENGINE_URL", default=None)
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
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")

# if PROD:
#     CLOUDRUN_SERVICE_URL = os.getenv("CLOUDRUN_SERVICE_URL", default=None)
#     if CLOUDRUN_SERVICE_URL:
#         ALLOWED_HOSTS = [urlparse(CLOUDRUN_SERVICE_URL).netloc]
#         CSRF_TRUSTED_ORIGINS = [CLOUDRUN_SERVICE_URL]
#         SECURE_SSL_REDIRECT = True
#         SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
#     else:
#         ALLOWED_HOSTS = ["*"]
# else:
#     ALLOWED_HOSTS = ["*"]

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
    #'compressor',
    #'sass_processor',
    'simple_history',
    'social_django',
    'template_partials',
    #'colorfield', # pip install django-colorfield
    #'easy_timezones', # pip install django-easy-timezones
]

if USE_SASS:
    INSTALLED_APPS.append('compressor')
    INSTALLED_APPS.append('sass_processor')

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
    DATABASES = {"default": dj_database_url.parse(os.getenv("DATABASE_URL"))}

    # if os.getenv("USE_CLOUD_SQL_AUTH_PROXY", None):
    #     DATABASES["default"]["HOST"] = "127.0.0.1"
    #     DATABASES["default"]["PORT"] = 5432
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

STATIC_URL = "static/"

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

if PROD:
    # this is what whitenoise uses (for prod)
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    if USE_SASS:
        SASS_PROCESSOR_ROOT = STATIC_ROOT
else:
    # this only applies if debug=true
    if USE_SASS:
        COMPRESS_ROOT = STATICFILES_DIRS[0]
        SASS_PROCESSOR_ROOT = STATICFILES_DIRS[0]
    # comment out the above and uncomment the below when collecting static
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / '/uploads/'

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]


if USE_SASS:
    STATICFILES_FINDERS.append('compressor.finders.CompressorFinder')
    STATICFILES_FINDERS.append('sass_processor.finders.CssFinder')


if USE_SASS:
    COMPRESS_PRECOMPILERS = ( 
        ('text/x-scss', 'sass {infile} {outfile}'), 
    )
    COMPRESS_ENABLED = True
else:
    COMPRESS_ENABLED = False
    # COMPRESS_PRECOMPILERS = [
    #         ('text/x-scss', 'django_libsass.SassCompiler'),
    # ]


GS_DEFAULT_ACL = "publicRead"

# for message framework
# the django red alert class is called "danger", django calls it "error"
# this changes it so it uses danger (for the bootstrap class)
MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}

SHOW_TOOLBAR_CALLBACK = lambda request: request.user.is_superuser

LOGIN_REDIRECT_URL = '/'

LOGIN_URL = '/accounts/login/'

# SOCIAL_AUTH_GOOGLE_OAUTH_KEY = ''
# SOCIAL_AUTH_GOOGLE_OAUTH_SECRET = ''
SOCIAL_AUTH_URL_NAMESPACE = 'social'
SOCIAL_AUTH_JSONFIELD_ENABLED = True
SOCIAL_AUTH_REDIRECT_IS_HTTPS = True

X_FRAME_OPTIONS = 'SAMEORIGIN'

# insert urls here
# EVERY TIME URL CHANGES, UPDATE THIS LIST W/ NEW URL!!!!!!
CSRF_TRUSTED_ORIGINS = [
    'https://compserver.ucls.uchicago.edu',
    'https://compserver-7bc24fc483a9.herokuapp.com/',
    #'https://compserver-service-hoxlb46hdq-uc.a.run.app'
    #'https://compserver-service-84176890180.us-central1.run.app',
    #"https://compserver-service-hoxlb46hdq-uc.a.run.app",
]


AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'social_core.backends.gitlab.GitLabOAuth2',
    'social_core.backends.github.GithubOAuth2',
    'social_core.backends.google.GoogleOAuth2',
    #'rest_framework_social_oauth2.backends.DjangoOAuth2',
)
    

if USE_SENTRY:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    assert SENTRY_URL is not None, "Sentry URL must be set if USE_SENTRY = True"
    sentry_sdk.init(
        dsn=SENTRY_URL, # maybe we put this url in a secret?

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
        release=RELEASE_VERSION,
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

