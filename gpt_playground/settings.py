"""
Django settings for GPT Playground project.

Generated by 'django-admin startproject' using Django 3.2.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

import os
import sys
from pathlib import Path

import environ
from django.utils.translation import gettext_lazy

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
env.read_env(os.path.join(BASE_DIR, ".env"))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY", default="YNAazYQdzqQWddeZmFZfBfROzqlzvLEwVxoOjGgK")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
IS_TESTING = "pytest" in sys.modules

ALLOWED_HOSTS = ["*"]
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# Application definition

DJANGO_APPS = [
    # "django.contrib.admin",  # replaced by "apps.web.apps.OcsAdminConfig"
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.humanize",
    "django.contrib.sessions",
    "django.contrib.sitemaps",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.forms",
]

# Put your third-party apps here
THIRD_PARTY_APPS = [
    "allauth",  # allauth account/registration management
    "allauth.account",
    "allauth.socialaccount",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "django_otp.plugins.otp_static",
    "allauth_2fa",
    "rest_framework",
    "drf_spectacular",
    "rest_framework_api_key",
    "celery_progress",
    "hijack",  # "login as" functionality
    "hijack.contrib.admin",  # hijack buttons in the admin
    "whitenoise.runserver_nostatic",  # whitenoise runserver
    "waffle",
    "django_celery_beat",
    "django_tables2",
    "field_audit",
    "taggit",
    "tz_detect",
    "health_check",
    "health_check.db",
    "health_check.cache",
    "health_check.contrib.celery",
    "health_check.contrib.redis",
    "template_partials",
]

PROJECT_APPS = [
    "apps.web.apps.OcsAdminConfig",
    "apps.audit",
    "apps.users",
    "apps.api",
    "apps.chat",
    "apps.custom_actions",
    "apps.experiments",
    "apps.web.apps.WebConfig",
    "apps.teams",
    "apps.channels",
    "apps.service_providers",
    "apps.analysis",
    "apps.generics",
    "apps.assistants",
    "apps.files",
    "apps.events",
    "apps.annotations",
    "apps.pipelines",
    "apps.slack",
    "apps.participants",
]

SPECIAL_APPS = [
    "django_cleanup"  # according to the docs, this should be the last app installed
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + PROJECT_APPS + SPECIAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "apps.teams.middleware.TeamsMiddleware",
    "apps.web.scope_middleware.RequestContextMiddleware",
    "apps.web.locale_middleware.UserLocaleMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "hijack.middleware.HijackUserMiddleware",
    "waffle.middleware.WaffleMiddleware",
    "field_audit.middleware.FieldAuditMiddleware",
    "apps.audit.middleware.AuditTransactionMiddleware",
    "apps.web.htmx_middleware.HtmxMessageMiddleware",
    "tz_detect.middleware.TimezoneMiddleware",
]

ROOT_URLCONF = "gpt_playground.urls"

# used to disable the cache in dev, but turn it on in production.
# more here: https://nickjanetakis.com/blog/django-4-1-html-templates-are-cached-by-default-with-debug-true
_DEFAULT_LOADERS = [
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
]

_CACHED_LOADERS = [("django.template.loaders.cached.Loader", _DEFAULT_LOADERS)]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.web.context_processors.project_meta",
                "apps.teams.context_processors.team",
                "apps.users.context_processors.user_teams",
                # this line can be removed if not using google analytics
                "apps.web.context_processors.google_analytics_id",
            ],
            "loaders": _DEFAULT_LOADERS if DEBUG else _CACHED_LOADERS,
            "builtins": [
                "apps.web.templatetags.default_tags",
                "template_partials.templatetags.partials",
            ],
        },
    },
]

WSGI_APPLICATION = "gpt_playground.wsgi.application"

FORM_RENDERER = "django.forms.renderers.TemplatesSetting"
FORMS_URLFIELD_ASSUME_HTTPS = True

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

if "DATABASE_URL" in env:
    DATABASES = {"default": env.db()}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "NAME": env("DJANGO_DATABASE_NAME", default="gpt_playground"),
            "USER": env("DJANGO_DATABASE_USER", default="postgres"),
            "PASSWORD": env("DJANGO_DATABASE_PASSWORD", default="***"),
            "HOST": env("DJANGO_DATABASE_HOST", default="localhost"),
            "PORT": env("DJANGO_DATABASE_PORT", default="5432"),
        }
    }

# Auth / login stuff

# Django recommends overriding the user model even if you don't think you need to because it makes
# future changes much easier.
AUTH_USER_MODEL = "users.CustomUser"
LOGIN_URL = "account_login"
LOGIN_REDIRECT_URL = "/"

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Allauth setup
SIGNUP_ENABLED = env("SIGNUP_ENABLED", default=False)
if SIGNUP_ENABLED:
    ACCOUNT_ADAPTER = "apps.teams.adapter.AcceptInvitationAdapter"
else:
    ACCOUNT_ADAPTER = "apps.users.adapter.NoNewUsersAccountAdapter"
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_SUBJECT_PREFIX = ""
ACCOUNT_CONFIRM_EMAIL_ON_GET = False
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = False
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_FORMS = {
    "signup": "apps.teams.forms.TeamSignupForm",
}

# User signup configuration: change to "mandatory" to require users to confirm email before signing in.
# or "optional" to send confirmation emails but not require them
ACCOUNT_EMAIL_VERIFICATION = env("ACCOUNT_EMAIL_VERIFICATION", default="optional")

ALLAUTH_2FA_ALWAYS_REVEAL_BACKUP_TOKENS = False

AUTHENTICATION_BACKENDS = (
    # check permissions exist (DEBUG only)
    "apps.teams.backends.PermissionCheckBackend",
    # login etc. + team membership based permissions
    "apps.teams.backends.TeamBackend",
    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend",
)

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-us"
LANGUAGE_COOKIE_NAME = "gpt_playground_language"
LANGUAGES = [
    ("en", gettext_lazy("English")),
]
LOCALE_PATHS = (BASE_DIR / "locale",)

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/ref/contrib/staticfiles/

STATIC_ROOT = BASE_DIR / "static_root"
STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "public": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# File storage: https://docs.djangoproject.com/en/4.2/topics/files/

MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", default=None)
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", default=None)
AWS_S3_REGION = env("AWS_S3_REGION", default=None)
WHATSAPP_S3_AUDIO_BUCKET = env("WHATSAPP_S3_AUDIO_BUCKET", default=None)

USE_S3_STORAGE = env.bool("USE_S3_STORAGE", default=False)
if USE_S3_STORAGE:
    # match names in django-storages
    AWS_S3_ACCESS_KEY_ID = AWS_ACCESS_KEY_ID
    AWS_S3_REGION_NAME = AWS_S3_REGION

    # use private storage by default
    STORAGES["default"] = {
        "BACKEND": "apps.web.storage_backends.PrivateMediaStorage",
        "OPTIONS": {
            "bucket_name": env("AWS_PRIVATE_STORAGE_BUCKET_NAME"),
            "location": "resources",
        },
    }

    # public storge for media files e.g. user profile pictures
    AWS_PUBLIC_STORAGE_BUCKET_NAME = env("AWS_PUBLIC_STORAGE_BUCKET_NAME")
    PUBLIC_MEDIA_LOCATION = "media"
    MEDIA_URL = f"https://{AWS_PUBLIC_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{PUBLIC_MEDIA_LOCATION}/"
    STORAGES["public"] = {
        "BACKEND": "apps.web.storage_backends.PublicMediaStorage",
        "OPTIONS": {
            "bucket_name": AWS_PUBLIC_STORAGE_BUCKET_NAME,
            "location": PUBLIC_MEDIA_LOCATION,
        },
    }

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Email setup

# use in development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
# use in production
# see https://github.com/anymail/django-anymail for more details/examples
# EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"

# Django sites

SITE_ID = 1

# DRF config
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.api.permissions.ApiKeyAuthentication",
        "apps.api.permissions.BearerTokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "apps.api.pagination.CursorPagination",
    "PAGE_SIZE": 100,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Dimagi Chatbots",
    "DESCRIPTION": "Experiments with AI, GPT and LLMs",
    "VERSION": "1",
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_SETTINGS": {
        "displayOperationId": True,
    },
}

# Celery setup (using redis)
if "REDIS_URL" in env:
    REDIS_URL = env("REDIS_URL")
elif "REDIS_TLS_URL" in env:
    REDIS_URL = env("REDIS_TLS_URL")
else:
    REDIS_HOST = env("REDIS_HOST", default="localhost")
    REDIS_PORT = env("REDIS_PORT", default="6379")
    REDIS_SCHEME = "rediss" if env.bool("REDIS_USE_TLS", False) else "redis"
    REDIS_URL = f"{REDIS_SCHEME}://{REDIS_HOST}:{REDIS_PORT}/0"

if REDIS_URL.startswith("rediss"):
    REDIS_URL = f"{REDIS_URL}?ssl_cert_reqs=none"

CELERY_BROKER_URL = CELERY_RESULT_BACKEND = REDIS_URL
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "health_check_interval": 30,
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },
}

# Waffle config
WAFFLE_FLAG_MODEL = "teams.Flag"
WAFFLE_CREATE_MISSING_FLAGS = True

# replace any values below with specifics for your project
PROJECT_METADATA = {
    "NAME": gettext_lazy("Dimagi Chatbots"),
    "URL": "http://localhost:8000",
    "DESCRIPTION": gettext_lazy("Experiments with AI, GPT and LLMs"),
    "CONTACT_EMAIL": "devops+openchatstudio@dimagi.com",
    "IMAGE": "https://chatbots.dimagi.com/static/images/dimagi-logo.png",
    "TERMS_URL": env("TERMS_URL", default=""),
    "PRIVACY_POLICY_URL": env("PRIVACY_POLICY_URL", default=""),
}

USE_HTTPS_IN_ABSOLUTE_URLS = False  # set this to True in production to have URLs generated with https instead of http

ADMINS = [("Dimagi Admins", "devops+openchatstudio@dimagi.com")]

# Add your google analytics ID to the environment to connect to Google Analytics
GOOGLE_ANALYTICS_ID = env("GOOGLE_ANALYTICS_ID", default="")

# Sentry setup

# populate this to configure sentry. should take the form: 'https://****@sentry.io/12345'
SENTRY_DSN = env("SENTRY_DSN", default="")

if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        send_default_pii=True,  # include user details in events
        environment=env("SENTRY_ENVIRONMENT", default="development"),
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
        ],
    )

# Taskbadger setup
TASKBADGER_ORG = env("TASKBADGER_ORG", default=None)
TASKBADGER_PROJECT = env("TASKBADGER_PROJECT", default=None)
TASKBADGER_API_KEY = env("TASKBADGER_API_KEY", default=None)

if TASKBADGER_ORG and TASKBADGER_PROJECT and TASKBADGER_API_KEY:
    import taskbadger
    from taskbadger.systems.celery import CelerySystemIntegration

    taskbadger.init(
        organization_slug=TASKBADGER_ORG,
        project_slug=TASKBADGER_PROJECT,
        token=TASKBADGER_API_KEY,
        systems=[
            CelerySystemIntegration(
                excludes=[
                    # ignore these since they execute often and fire other tasks that we already track
                    "apps.events.tasks.enqueue_static_triggers",
                    "apps.events.tasks.enqueue_timed_out_events",
                ]
            )
        ],
    )

LOG_LEVEL = env("OCS_LOG_LEVEL", default="DEBUG" if DEBUG else "INFO")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": '[{asctime}] {levelname} "{name}" {message}',
            "style": "{",
            "datefmt": "%d/%b/%Y %H:%M:%S",  # match Django server time format
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": env("DJANGO_LOG_LEVEL", default="INFO"),
        },
        "ocs": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": IS_TESTING},
        "httpx": {"handlers": ["console"], "level": "WARN"},
        "slack_bolt": {"handlers": ["console"], "level": "DEBUG"},
    },
}

# Telegram webhook config
TELEGRAM_SECRET_TOKEN = env("TELEGRAM_SECRET_TOKEN", default="")

# Django tables

DJANGO_TABLES2_TEMPLATE = "table/tailwind.html"
DJANGO_TABLES2_TABLE_ATTRS = {
    "class": "w-full table-fixed",
    "thead": {"class": "bg-base-200 base-content uppercase text-sm leading-normal"},
    "th": {"class": "py-3 px-3 text-left"},
    "td": {"class": "py-3 px-3 text-left overflow-hidden"},
}
# text-neutral text-error (pipeline run table styles here for tailwind build)
DJANGO_TABLES2_ROW_ATTRS = {
    "class": """
        border-b border-base-300 hover:bg-base-200
        data-[redirect-url]:[&:not([data-redirect-url=''])]:hover:cursor-pointer
    """,
    "id": lambda record: f"record-{record.id}",
    "data-redirect-url": lambda record: record.get_absolute_url() if hasattr(record, "get_absolute_url") else "",
}

# This is only used for development purposes
SITE_URL_ROOT = env("SITE_URL_ROOT", default=None)

# Taggit
TAGGIT_CASE_INSENSITIVE = True

# Documentation links
DOCUMENTATION_LINKS = {
    "consent": "https://dimagi.atlassian.net/wiki/spaces/OCS/pages/2144305304/Consent+Forms+on+OCS",
    "survey": "https://dimagi.atlassian.net/wiki/spaces/OCS/pages/2144305308/Surveys",
    "experiment": "https://dimagi.atlassian.net/wiki/spaces/OCS/pages/2144305312/Creating+a+Chatbot+Experiment",
}
DOCUMENTATION_BASE_URL = env("DOCUMENTATION_BASE_URL", default="https://dimagi.github.io/open-chat-studio-docs")

# Django rest framework config
API_KEY_CUSTOM_HEADER = "HTTP_X_API_KEY"

# Django Field Audit
FIELD_AUDIT_AUDITORS = ["apps.audit.auditors.AuditContextProvider"]
FIELD_AUDIT_TEAM_EXEMPT_VIEWS = [
    "account_reset_password_from_key",
    "teams:signup_after_invite",
    "account_login",
]
FIELD_AUDIT_REQUEST_ID_HEADERS = [
    "X-Request-ID",  # Heroku
    "X-Amzn-Trace-Id",  # Amazon
    "traceparent",  # W3C Trace Context (Google)
]
TEST_NON_SERIALIZED_APPS = [
    "field_audit",
]

# tz_detect
TZ_DETECT_COUNTRIES = ["US", "IN", "GB", "ZA", "KE"]

# slack
SLACK_CLIENT_ID = env("SLACK_CLIENT_ID", default="")
SLACK_CLIENT_SECRET = env("SLACK_CLIENT_SECRET", default="")
SLACK_SIGNING_SECRET = env("SLACK_SIGNING_SECRET", default="")
SLACK_SCOPES = [
    "channels:history",
    "channels:join",
    "channels:read",
    "chat:write",
    "chat:write.public",
    "groups:history",
    "groups:read",
    "im:history",
    "im:read",
    "mpim:history",
    "mpim:read",
    "users.profile:read",
]
SLACK_BOT_NAME = env("SLACK_BOT_NAME", default="@ocs")
SLACK_ENABLED = SLACK_CLIENT_ID and SLACK_CLIENT_SECRET and SLACK_SIGNING_SECRET

# Health checks
# Tokens used to secure the /status endpoint. These should be kept secret
HEALTH_CHECK_TOKENS = env.list("HEALTH_CHECK_TOKENS", default=[])
HEALTH_CHECK = {
    "SUBSETS": {
        "general": ["Cache backend: default", "DatabaseBackend", "RedisHealthCheck"],
        "celery": ["CeleryHealthCheckCelery"],
    },
}

CRYPTOGRAPHY_SALT = env("CRYPTOGRAPHY_SALT", default="")

PUBLIC_CHAT_LINK_MAX_AGE = 5  # 5 minutes
