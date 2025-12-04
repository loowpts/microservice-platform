# Руководство по разработке

Это руководство описывает процесс разработки и лучшие практики для работы с микросервисной платформой.

## Содержание

- [Настройка окружения](#настройка-окружения)
- [Структура проекта](#структура-проекта)
- [Разработка нового микросервиса](#разработка-нового-микросервиса)
- [Работа с базами данных](#работа-с-базами-данных)
- [Тестирование](#тестирование)
- [Стиль кода](#стиль-кода)
- [Git Workflow](#git-workflow)
- [Отладка](#отладка)
- [Лучшие практики](#лучшие-практики)

## Настройка окружения

### Требования

- Python 3.11+
- Docker 20.10+
- Docker Compose 2.0+
- Git
- IDE (рекомендуется VS Code или PyCharm)

### Установка для разработки

1. **Клонирование репозитория:**

```bash
git clone https://github.com/loowpts/microservice-platform.git
cd microservice-platform
```

2. **Создание виртуального окружения (опционально, для IDE):**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Установка зависимостей для IDE:**

```bash
pip install -r services/user-service/requirements.txt
# Повторить для других сервисов при необходимости
```

4. **Настройка переменных окружения:**

```bash
cp .env.example .env
# Отредактировать .env для разработки
```

5. **Запуск сервисов:**

```bash
docker-compose up -d
```

### VS Code настройка

Рекомендуемые расширения:

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-azuretools.vscode-docker",
    "njpwerner.autodocstring",
    "esbenp.prettier-vscode",
    "ms-python.black-formatter"
  ]
}
```

Создайте `.vscode/settings.json`:

```json
{
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "100"],
  "editor.formatOnSave": true,
  "editor.rulers": [100],
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  }
}
```

### PyCharm настройка

1. Откройте проект в PyCharm
2. Settings → Project → Python Interpreter
3. Добавьте Docker Compose интерпретатор
4. Настройте автоформатирование с Black

## Структура проекта

```
microservice-platform/
├── services/                  # Все микросервисы
│   ├── api-gateway/
│   │   ├── apps/
│   │   │   ├── gateway/      # Основное приложение
│   │   │   └── middleware/   # Middleware
│   │   ├── config/           # Django конфигурация
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── manage.py
│   │
│   ├── user-service/
│   │   ├── apps/
│   │   │   ├── users/        # Основное приложение
│   │   │   └── common/       # Общие утилиты
│   │   ├── config/
│   │   ├── tests/            # Тесты
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── pytest.ini
│   │   └── manage.py
│   │
│   └── ... (другие сервисы с аналогичной структурой)
│
├── docs/                     # Документация
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── DEPLOYMENT.md
│   ├── DEVELOPMENT.md
│   └── services/            # Документация по сервисам
│
├── docker-compose.yml        # Development compose
├── docker-compose.prod.yml   # Production compose
├── init-databases.sql        # SQL инициализация
├── .env                      # Переменные окружения
├── .gitignore
└── README.md
```

### Структура Django сервиса

```
service-name/
├── apps/                    # Django приложения
│   ├── main_app/
│   │   ├── __init__.py
│   │   ├── models.py       # Модели данных
│   │   ├── views.py        # API views
│   │   ├── urls.py         # URL маршруты
│   │   ├── serializers.py  # DRF serializers (если есть)
│   │   ├── forms.py        # Django формы
│   │   ├── admin.py        # Django admin
│   │   ├── signals.py      # Django signals
│   │   ├── tasks.py        # Celery tasks
│   │   ├── tests/          # Тесты
│   │   │   ├── __init__.py
│   │   │   ├── test_models.py
│   │   │   ├── test_views.py
│   │   │   └── factories.py  # Factory Boy
│   │   └── migrations/     # Миграции БД
│   │
│   └── common/              # Общие утилиты
│       ├── api.py          # API интеграции
│       ├── decorators.py   # Декораторы
│       ├── middleware.py   # Middleware
│       └── utils.py        # Утилиты
│
├── config/                  # Django настройки
│   ├── __init__.py
│   ├── settings.py         # Основные настройки
│   ├── urls.py             # Главные URL
│   ├── wsgi.py
│   └── asgi.py
│
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── requirements.txt
├── pytest.ini              # Pytest конфигурация
├── .dockerignore
└── manage.py
```

## Разработка нового микросервиса

### 1. Создание структуры

```bash
# Создать директорию
mkdir -p services/new-service

# Создать Django проект
cd services/new-service
django-admin startproject config .

# Создать приложение
python manage.py startapp main_app
mv main_app apps/
```

### 2. Конфигурация Django

**config/settings.py:**

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')

# Applications
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third party
    'rest_framework',
    'corsheaders',
    # Local apps
    'apps.main_app',
    'apps.common',
]

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB'),
        'USER': os.environ.get('POSTGRES_USER'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
        'HOST': os.environ.get('POSTGRES_HOST'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}

# Redis
REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
}

# CORS
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
CORS_ALLOW_CREDENTIALS = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

### 3. Создание Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

EXPOSE 8005

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8005/api/health/ || exit 1

ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8005", "--workers", "3"]
```

### 4. entrypoint.sh

```bash
#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
  sleep 0.1
done
echo "PostgreSQL started"

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting server..."
exec "$@"
```

### 5. requirements.txt

```txt
Django==5.2.5
djangorestframework==3.14.0
psycopg2-binary==2.9.9
redis==5.0.1
django-redis==6.0.0
celery==5.3.4
django-cors-headers==4.3.1
gunicorn==21.2.0
whitenoise==6.11.0
python-dotenv==1.1.1
requests==2.31.0

# Testing
pytest==7.4.4
pytest-django==4.7.0
pytest-cov==4.1.0
factory-boy==3.3.0
faker==22.0.0
```

### 6. Добавление в docker-compose.yml

```yaml
  new-service:
    build:
      context: ./services/new-service
      dockerfile: Dockerfile
    container_name: new_service
    restart: unless-stopped
    expose:
      - "8005"
    environment:
      - DEBUG=${DEBUG:-True}
      - SECRET_KEY=${SECRET_KEY}
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_DB=${NEW_SERVICE_DB_NAME:-new_service_db}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - REDIS_URL=redis://redis:6379/6
    volumes:
      - new_service_media:/app/media
      - new_service_static:/app/staticfiles
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - microservices_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8005/api/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### 7. Добавление в API Gateway

**apps/gateway/router.py:**

```python
SERVICE_ROUTES = {
    # ... существующие маршруты
    '/api/newservice/': settings.NEW_SERVICE_URL,
}
```

### 8. Создание БД в init-databases.sql

```sql
-- Добавить в init-databases.sql
CREATE DATABASE new_service_db;

\c new_service_db;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
```

## Работа с базами данных

### Создание модели

```python
# apps/main_app/models.py
from django.db import models
import uuid

class MyModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'my_models'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return self.name
```

### Создание миграции

```bash
# Создать миграцию
docker-compose exec new-service python manage.py makemigrations

# Просмотр SQL
docker-compose exec new-service python manage.py sqlmigrate main_app 0001

# Применить миграции
docker-compose exec new-service python manage.py migrate

# Откат
docker-compose exec new-service python manage.py migrate main_app 0001
```

### Django Shell

```bash
# Войти в shell
docker-compose exec new-service python manage.py shell

# В shell
>>> from apps.main_app.models import MyModel
>>> MyModel.objects.create(name="Test")
>>> MyModel.objects.all()
```

### Работа с PostgreSQL

```bash
# Подключиться к БД
docker-compose exec postgres psql -U postgres -d new_service_db

# SQL запросы
SELECT * FROM my_models;

# Экспорт данных
docker-compose exec postgres pg_dump -U postgres new_service_db > backup.sql

# Импорт данных
cat backup.sql | docker-compose exec -T postgres psql -U postgres -d new_service_db
```

## Тестирование

### Настройка pytest

**pytest.ini:**

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
python_files = tests.py test_*.py *_tests.py
addopts =
    --verbose
    --strict-markers
    --tb=short
    --cov=apps
    --cov-report=html
    --cov-report=term-missing
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
```

### Написание тестов

**apps/main_app/tests/factories.py:**

```python
import factory
from factory.django import DjangoModelFactory
from apps.main_app.models import MyModel

class MyModelFactory(DjangoModelFactory):
    class Meta:
        model = MyModel

    name = factory.Faker('word')
    description = factory.Faker('text')
```

**apps/main_app/tests/test_models.py:**

```python
import pytest
from apps.main_app.tests.factories import MyModelFactory

@pytest.mark.django_db
class TestMyModel:
    def test_create_model(self):
        """Тест создания модели"""
        obj = MyModelFactory()
        assert obj.id is not None
        assert obj.name is not None

    def test_str_representation(self):
        """Тест строкового представления"""
        obj = MyModelFactory(name="Test Name")
        assert str(obj) == "Test Name"
```

**apps/main_app/tests/test_views.py:**

```python
import pytest
from django.urls import reverse

@pytest.mark.django_db
class TestMyModelViews:
    def test_list_view(self, client):
        """Тест списка объектов"""
        MyModelFactory.create_batch(3)

        url = reverse('mymodel-list')
        response = client.get(url)

        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_create_view(self, client):
        """Тест создания объекта"""
        url = reverse('mymodel-list')
        data = {'name': 'Test', 'description': 'Test desc'}

        response = client.post(url, data, content_type='application/json')

        assert response.status_code == 201
        assert response.json()['name'] == 'Test'
```

### Запуск тестов

```bash
# Все тесты
docker-compose exec new-service pytest

# Конкретный файл
docker-compose exec new-service pytest apps/main_app/tests/test_models.py

# Конкретный тест
docker-compose exec new-service pytest apps/main_app/tests/test_models.py::TestMyModel::test_create_model

# С покрытием
docker-compose exec new-service pytest --cov=apps --cov-report=html

# С выводом print
docker-compose exec new-service pytest -s

# Только failed тесты
docker-compose exec new-service pytest --lf

# Параллельное выполнение
docker-compose exec new-service pytest -n auto
```

## Стиль кода

### Black

```bash
# Форматирование файла
black apps/main_app/models.py

# Форматирование всего проекта
black .

# Проверка без изменений
black --check .
```

### Flake8

```bash
# Проверка стиля
flake8 apps/

# С конфигурацией
flake8 --max-line-length=100 --exclude=migrations apps/
```

**.flake8:**

```ini
[flake8]
max-line-length = 100
exclude =
    migrations,
    __pycache__,
    manage.py,
    settings.py
ignore = E203, E266, E501, W503
```

### isort

```bash
# Сортировка импортов
isort apps/

# Проверка
isort --check-only apps/
```

## Git Workflow

### Branch Strategy

```
main          - production код
develop       - development код
feature/*     - новые функции
bugfix/*      - исправление багов
hotfix/*      - срочные исправления
```

### Commit Messages

Используйте conventional commits:

```
feat: добавить новый endpoint для заказов
fix: исправить ошибку в валидации email
docs: обновить API документацию
test: добавить тесты для User model
refactor: переработать структуру views
chore: обновить зависимости
```

### Workflow

```bash
# Создать feature branch
git checkout -b feature/new-feature develop

# Работа над фичей
git add .
git commit -m "feat: добавить новую функцию"

# Push в remote
git push origin feature/new-feature

# Создать Pull Request на GitHub
# После review - merge в develop

# Для release
git checkout main
git merge develop
git tag v1.0.0
git push origin main --tags
```

## Отладка

### Django Debug Toolbar

Добавить в development:

```python
# settings.py
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1']
```

### Логирование

```python
import logging

logger = logging.getLogger(__name__)

def my_view(request):
    logger.info(f"Processing request for user {request.user.id}")
    try:
        # код
        logger.debug("Debug information")
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}", exc_info=True)
```

### pdb

```python
# Добавить breakpoint
import pdb; pdb.set_trace()

# Или Python 3.7+
breakpoint()
```

### Docker logs

```bash
# Real-time логи
docker-compose logs -f new-service

# Поиск в логах
docker-compose logs new-service | grep "ERROR"

# Логи за период
docker-compose logs --since 30m new-service
```

## Лучшие практики

### 1. Код

- Следуйте PEP 8
- Используйте type hints
- Пишите docstrings
- DRY (Don't Repeat Yourself)
- SOLID принципы

### 2. База данных

- Используйте индексы
- Избегайте N+1 запросов (select_related, prefetch_related)
- Используйте транзакции где нужно
- Регулярные backup

### 3. API

- REST best practices
- Версионирование API
- Валидация входных данных
- Правильные HTTP статусы
- Pagination для списков

### 4. Безопасность

- Никогда не коммитить секреты
- Валидация на backend
- SQL injection защита (ORM)
- XSS защита
- CSRF защита

### 5. Тестирование

- Минимум 80% покрытие
- Unit, Integration, E2E тесты
- Тестировать edge cases
- Использовать фикстуры и фабрики

### 6. Docker

- Multi-stage builds
- Минимальные образы (alpine)
- .dockerignore
- Health checks
- Resource limits

## CI/CD

Пример GitHub Actions:

**.github/workflows/test.yml:**

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r services/user-service/requirements.txt

      - name: Run tests
        run: |
          cd services/user-service
          pytest --cov=apps --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## См. также

- [README](../README.md)
- [Архитектура](ARCHITECTURE.md)
- [Deployment](DEPLOYMENT.md)
- [API документация](API.md)
