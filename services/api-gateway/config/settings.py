import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'corsheaders',
    'apps.gateway',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.middleware.logging_middleware.LoggingMiddleware',
    'apps.middleware.auth_middleware.JWTAuthMiddleware',
    'apps.middleware.rate_limit_middleware.RateLimitMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {}

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'gateway',
    }
}

USER_SERVICE_URL = os.getenv('USER_SERVICE_URL', 'http://localhost:8000')
FREELANCE_SERVICE_URL = os.getenv('FREELANCE_SERVICE_URL', 'http://localhost:8002')
NOTIFICATION_SERVICE_URL = os.getenv('NOTIFICATION_SERVICE_URL', 'http://localhost:8001')
CONTENT_SERVICE_URL = os.getenv('CONTENT_SERVICE_URL', 'http://localhost:8003')
MARKETPLACE_SERVICE_URL = os.getenv('MARKETPLACE_SERVICE_URL', 'http://localhost:8004')

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
JWT_ALGORITHM = 'HS256'

RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', 1000))
RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', 60))
RATE_LIMIT_BURST = int(os.getenv('RATE_LIMIT_BURST', 100))

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

(BASE_DIR / 'staticfiles').mkdir(exist_ok=True, parents=True)

SILENCED_SYSTEM_CHECKS = ['admin.E408', 'admin.E409', 'admin.E410']

REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 30))
HEALTH_CHECK_ENABLED = os.getenv('HEALTH_CHECK_ENABLED', 'True').lower() == 'true'
