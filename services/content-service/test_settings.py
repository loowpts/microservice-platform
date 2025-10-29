from config.settings import *

# Используем in-memory SQLite для быстрых тестов
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR.parent.parent / 'databases' / 'test.db',
    }
}

# Отключаем миграции для ускорения тестов
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Используем более быстрый хэшер паролей для тестов
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Отключаем логирование в тестах
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
        'level': 'CRITICAL',
    },
}

# Отключаем DEBUG для тестов
DEBUG = False

# Простой SECRET_KEY для тестов
SECRET_KEY = 'test-secret-key-for-testing-only'

# Отключаем внешние запросы в тестах
USER_SERVICE_URL = 'http://mock-user-service:8000'
SERVICE_TOKEN = 'test-token'

# Redis для тестов (можно использовать fake redis)
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 15  # Отдельная БД для тестов

# Отключаем CSRF для API тестов
CSRF_USE_SESSIONS = False
CSRF_COOKIE_HTTPONLY = False
