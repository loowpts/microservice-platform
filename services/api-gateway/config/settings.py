import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'api-gateway-secret-key-change-in-production')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '*']

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
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    'apps.middleware.logging_middleware.LoggingMiddleware',       # Логирование
    'apps.middleware.auth_middleware.JWTAuthMiddleware',          # Аутентификация
    'apps.middleware.rate_limit_middleware.RateLimitMiddleware',  # Rate limiting
    
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


# Для разработки - разрешить все домены
CORS_ALLOW_ALL_ORIGINS = True

# Для продакшена - только конкретные домены
# CORS_ALLOWED_ORIGINS = [
#     'http://localhost:3000',
#     'https://yourapp.com',
# ]

CORS_ALLOW_CREDENTIALS = True  # Для cookies и Authorization headers

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
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
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'gateway.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'gateway': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

USER_SERVICE_URL = os.getenv('USER_SERVICE_URL', 'http://localhost:8000')
FREELANCE_SERVICE_URL = os.getenv('FREELANCE_SERVICE_URL', 'http://localhost:8002')
NOTIFICATION_SERVICE_URL = os.getenv('NOTIFICATION_SERVICE_URL', 'http://localhost:8001')
CONTENT_SERVICE_URL = os.getenv('CONTENT_SERVICE_URL', 'http://localhost:8003')

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
JWT_ALGORITHM = 'HS256'

RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', 100))
RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', 60))

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Отключить проверки БД (т.к. БД нет)
SILENCED_SYSTEM_CHECKS = ['admin.E408', 'admin.E409', 'admin.E410']
