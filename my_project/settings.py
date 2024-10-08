import os
from pathlib import Path
from mongoengine import connect
from pymongo import MongoClient
import gridfs
from decouple import config
from corsheaders.defaults import default_headers

BASE_DIR = Path(__file__).resolve().parent.parent

# Secret Key
SECRET_KEY = config('SECRET_KEY')

# Debug mode
DEBUG = True  # Set to False in production for security reasons

# Allowed Hosts
ALLOWED_HOSTS = [
    '127.0.0.1',                   # Localhost for development
    'localhost',                   # Localhost for development
    'recipe-z.onrender.com',       # Production domain
    'recipe-z.com',               # Production domain
    'localhost:3000',             # React frontend during local development
    'recipe-z.vercel.app',         # Vercel frontend during production
]

# Spoonacular API Key
SPOONACULAR_API_KEY = config('SPOONACULAR_API_KEY')

# MongoDB Connection
connect(
    db='Recipe-z',
    host=config('MONGODB_URI'),
)

# GridFS Setup
client = MongoClient(config('MONGODB_URI'))
db = client['Recipe-z']
fs = gridfs.GridFS(db)

# Add GridFS to settings
GRIDFS_FS = fs

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'users',
    'rest_framework',
    'rest_framework.authtoken',
    'social_django',
    'drf_yasg',
    'corsheaders',
    'debug_toolbar',
]

AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.facebook.FacebookOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

# Google OAuth2 Configuration
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = config('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = config('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET')
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = ['email', 'profile']

# Facebook OAuth2 Configuration
SOCIAL_AUTH_FACEBOOK_KEY = config('SOCIAL_AUTH_FACEBOOK_KEY')
SOCIAL_AUTH_FACEBOOK_SECRET = config('SOCIAL_AUTH_FACEBOOK_SECRET')
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email', 'public_profile']

# Redirect URIs
# Adjust these based on the environment:
# For local development:
# FACEBOOK_REDIRECT_URI = 'http://127.0.0.1:8000/facebook/callback/'
# GOOGLE_REDIRECT_URI = 'http://localhost:8000/google/callback/'

# For production:
FACEBOOK_REDIRECT_URI = 'https://recipe-z.vercel.app/facebook/callback/'
GOOGLE_REDIRECT_URI = 'https://recipe-z.vercel.app/google/callback/'

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'METHOD': 'oauth2',
        'VERIFIED_EMAIL': False,
        'CLIENT_ID': config('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY'),
        'SECRET': config('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET'),
    },
    'facebook': {
        'METHOD': 'oauth2',
        'SCOPE': [
            'email',
            'public_profile',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'VERIFIED_EMAIL': False,
        'CLIENT_ID': config('SOCIAL_AUTH_FACEBOOK_KEY'),
        'SECRET': config('SOCIAL_AUTH_FACEBOOK_SECRET'),
    }
}

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # This should be at the top
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
    'users.views.TokenMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

INTERNAL_IPS = [
    '127.0.0.1',
]

# CORS settings

# For production:
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',        # React frontend during local development
    'https://recipe-z.vercel.app',  # Vercel frontend during production
]

CORS_ALLOW_CREDENTIALS = True  # Required for sending cookies (e.g., CSRF and auth token)

CORS_ALLOW_HEADERS = list(default_headers) + [
    'Authorization',  # Ensure proper casing for 'Authorization'
    'X-CSRFToken',    # Ensure proper casing for 'X-CSRFToken'
]

CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
    'OPTIONS',
]


# CSRF settings
# CSRF settings
CSRF_COOKIE_SAMESITE = 'None'
CSRF_COOKIE_SECURE = True  # Ensure this is True for HTTPS (production)

# Auth token settings
SESSION_COOKIE_SAMESITE = 'None'
SESSION_COOKIE_SECURE = True  # Ensure this is True for HTTPS (production)

CSRF_COOKIE_HTTPONLY = False  # To prevent CSRF cookie access from JavaScript
# Adjust these based on the environment:
# For local development:
# CSRF_TRUSTED_ORIGINS = ["http://localhost:3000"]

# For production:
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",  # React frontend during local development
    "https://recipe-z.vercel.app",  # Vercel frontend during production
]
CSRF_COOKIE_NAME = 'csrftoken'

ROOT_URLCONF = 'my_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'users/templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # 'social_django.context_processors.backends',
                # 'social_django.context_processors.login_redirect',
            ],
        },
    },
]

WSGI_APPLICATION = 'my_project.wsgi.application'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
}

# Use environment variable if available, otherwise default to relative path
CACHE_DIR = os.environ.get('CACHE_DIR', os.path.join(BASE_DIR, 'cache'))

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': CACHE_DIR,
        'TIMEOUT': 3600,  # Default cache timeout (1 hour)
        'OPTIONS': {
            'MAX_ENTRIES': 1000  # Adjust the number of cache entries based on your needs
        }
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
