"""
Django settings for the Findora Lost & Found Management application.
"""

import os
from pathlib import Path
from datetime import timedelta

from dotenv import load_dotenv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file for local development; on Render env vars are set via the Dashboard.
load_dotenv(BASE_DIR / '.env')

# ─── Security ────────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-fallback-key-change-me')
DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 'yes')
ALLOWED_HOSTS = ['*']

# ─── Application Definition ──────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',

    # Local
    'api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',          # Must be before CommonMiddleware
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',     # Add whitenoise for static files on Render
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Logs every request with timing — must be last so it wraps the full stack
    'api.middleware.RequestTimingMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

import sys

# ─── Database ────────────────────────────────────────────────────────────────
# Use in-memory SQLite during automated test runs for speed and isolation.
# DATABASE_URL is read from .env (local) or Render env vars (production).
# When DATABASE_URL is set, use PostgreSQL; otherwise fall back to SQLite for local dev.
if 'test' in sys.argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
elif os.environ.get('RENDER') or os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.parse(os.environ.get('DATABASE_URL', ''), conn_max_age=600)
    }
else:
    # If running locally on your PC, use SQLite so it doesn't crash trying to reach Render's internal network.
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
            'CONN_MAX_AGE': 0,
        }
    }

# ─── Custom User Model ───────────────────────────────────────────────────────
AUTH_USER_MODEL = 'api.User'

# ─── Password Validation ─────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ─── Django REST Framework ───────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ),
}

# ─── SimpleJWT Configuration ─────────────────────────────────────────────────
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# ─── CORS Configuration ──────────────────────────────────────────────────────
# Development: allow all origins (Android emulator, physical devices, Postman)
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# ─── Internationalization ────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ─── Static & Media Files ────────────────────────────────────────────────────
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ─── Backblaze B2 (S3-Compatible Media Storage) ──────────────────────────────
# When B2 credentials are provided via environment variables, django-storages
# uploads all media files (item images, profile pictures) directly to Backblaze B2.
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID') or os.environ.get('B2_APPLICATION_KEY_ID') or os.environ.get('B2_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY') or os.environ.get('B2_APPLICATION_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME') or os.environ.get('B2_BUCKET_NAME', 'findora-bucket')
AWS_S3_ENDPOINT_URL = os.environ.get('AWS_S3_ENDPOINT_URL') or os.environ.get('B2_ENDPOINT_URL', 'https://s3.eu-central-003.backblazeb2.com')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME') or os.environ.get('B2_REGION', 'eu-central-003')

USE_B2_STORAGE = bool(AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY)

WHITENOISE_MANIFEST_STRICT = False

if USE_B2_STORAGE:
    if 'storages' not in INSTALLED_APPS:
        INSTALLED_APPS.append('storages')

    AWS_DEFAULT_ACL = None
    AWS_S3_FILE_OVERWRITE = False
    AWS_S3_SIGNATURE_VERSION = 's3v4'
    AWS_QUERYSTRING_AUTH = True
    AWS_QUERYSTRING_EXPIRE = int(os.environ.get('AWS_QUERYSTRING_EXPIRE', 604800))  # 7 days signed URL expiration

    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
        },
    }
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
        },
    }

# ─── Email / Brevo Transactional API ─────────────────────────────────────────
# OTP emails are dispatched via Brevo's Transactional Email API in daemon
# threads (see api/utils.py) so the HTTP response is never blocked.
DEFAULT_FROM_EMAIL = 'Findora <rawatlaxman089@gmail.com>'

BREVO_API_KEY = os.environ.get("BREVO_API_KEY")

if not BREVO_API_KEY:
    import logging as _logging
    _logging.getLogger(__name__).warning(
        "BREVO_API_KEY is not set. OTP emails will NOT be sent. "
        "Add BREVO_API_KEY to your environment variables (Render Dashboard → Environment)."
    )

# ─── Khalti Payment Gateway ────────────────────────────────────────────────────
KHALTI_SECRET_KEY = os.environ.get('KHALTI_SECRET_KEY', 'test_secret_key')
PAYMENT_ENV = os.environ.get('PAYMENT_ENV', 'test').lower()

if PAYMENT_ENV == 'live':
    KHALTI_API_URL = "https://khalti.com/api/v2"
else:
    KHALTI_API_URL = "https://a.khalti.com/api/v2"

# ─── Logging ─────────────────────────────────────────────────────────────────
# Structured request logging so every API call is visible in the console with
# its endpoint, HTTP status, and elapsed time. Sensitive data (passwords, tokens)
# is never logged — the middleware filters those fields explicitly.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        # Django's built-in request logger (covers 4xx/5xx)
        'django.request': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        # Django's database query logger (DEBUG level shows each query + time)
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',   # Set to DEBUG to log every SQL query
            'propagate': False,
        },
        # Findora application loggers
        'api': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# ─── Default Primary Key ─────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'