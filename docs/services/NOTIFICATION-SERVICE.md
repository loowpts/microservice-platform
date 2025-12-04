# Notification Service

## Обзор

Notification Service отвечает за управление уведомлениями в системе. Сервис поддерживает множественные каналы доставки (email, in-app, push), асинхронную обработку через Celery, и предпочтения уведомлений пользователей.

## Основная информация

- **Порт:** 8001
- **Framework:** Django 5.2.5 + DRF 3.14.0
- **Язык:** Python 3.11
- **Database:** PostgreSQL
- **Cache:** Redis
- **Message Queue:** Celery + RabbitMQ/Redis
- **Task Broker:** Redis

## Архитектура

```
┌──────────────────────────────────────────┐
│    Notification Service :8001            │
├──────────────────────────────────────────┤
│  REST API Layer:                         │
│  - /api/notifications/                   │
│  - /api/notification-preferences/        │
│                                          │
│  Celery Tasks:                           │
│  - send_email_notification               │
│  - send_in_app_notification              │
│  - send_push_notification                │
│  - process_notification_batch            │
│                                          │
│  Models:                                 │
│  - Notification                          │
│  - NotificationPreference                │
└────────────┬────────────┬────────────────┘
             │            │
             ▼            ▼
        PostgreSQL    Redis (Celery)
        (storage)     (message queue)
```

## Структура проекта

```
notification-service/
├── apps/
│   ├── notifications/
│   │   ├── __init__.py
│   │   ├── models.py           # Notification, NotificationPreference
│   │   ├── views.py            # API views
│   │   ├── serializers.py       # DRF serializers
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── tasks.py            # Celery tasks
│   │   ├── services.py         # Business logic
│   │   ├── signals.py          # Django signals
│   │   ├── tests.py            # Unit tests
│   │   └── urls.py
│   └── __init__.py
├── config/
│   ├── __init__.py
│   ├── settings.py             # Django & Celery настройки
│   ├── urls.py                 # URL маршруты
│   ├── wsgi.py
│   └── asgi.py
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── celery_entrypoint.sh
├── manage.py
├── requirements.txt
└── celery_config.py
```

## Модели данных

### Notification

Основная модель для хранения уведомлений.

| Поле | Тип | Описание |
|------|-----|---------|
| id | Integer | Первичный ключ |
| user_id | Integer | ID пользователя (получатель) |
| type | CharField | Тип уведомления (email, in_app, push) |
| status | CharField | Статус (pending, sent, failed, read) |
| event | CharField | Тип события (order_created, review_received и т.д.) |
| title | CharField | Заголовок уведомления (макс. 200 символов) |
| message | TextField | Текст сообщения (макс. 2000 символов) |
| data | JSONField | Дополнительные данные в JSON формате |
| email_to | EmailField | Email адрес для отправки (если type='email') |
| email_subject | CharField | Тема email (макс. 200 символов) |
| email_html | TextField | HTML шаблон email |
| read_at | DateTime | Дата/время прочтения (null если не прочитано) |
| sent_at | DateTime | Дата/время отправки |
| error_message | TextField | Ошибка при отправке (если была) |
| created_at | DateTime | Дата создания |
| updated_at | DateTime | Дата последнего обновления |

**Методы:**
- `mark_as_read()` - отметить как прочитанное
- `mark_as_sent()` - отметить как отправленное
- `mark_as_failed(error)` - отметить как ошибка

**Индексы:**
- (user_id, status)
- (status)

### NotificationPreference

Модель для управления предпочтениями уведомлений.

| Поле | Тип | Описание |
|------|-----|---------|
| id | Integer | Первичный ключ |
| user_id | Integer | ID пользователя (unique) |
| email_enabled | Boolean | Включены ли email уведомления (default: True) |
| in_app_enabled | Boolean | Включены ли in-app уведомления (default: True) |
| push_enabled | Boolean | Включены ли push уведомления (default: True) |
| order_updates | Boolean | Уведомления об обновлении заказов (default: True) |
| review_updates | Boolean | Уведомления об отзывах (default: True) |
| message_updates | Boolean | Уведомления о сообщениях (default: True) |
| created_at | DateTime | Дата создания |
| updated_at | DateTime | Дата последнего обновления |

**Методы:**
- `is_channel_enabled(channel)` - проверить включен ли канал
- `get_enabled_channels()` - получить список включенных каналов

## API Endpoints

### Управление уведомлениями

#### Получить список уведомлений текущего пользователя

```http
GET /api/notifications/?page=1&status=unread&type=in_app
Authorization: Bearer {access_token}
```

**Query Parameters:**
- `page` (int) - номер страницы (default: 1)
- `status` (string) - фильтр по статусу (pending, sent, failed, read)
- `type` (string) - фильтр по типу (email, in_app, push)
- `event` (string) - фильтр по типу события
- `order_by` (string) - сортировка (-created_at, created_at, read_at)

**Response (200 OK):**
```json
{
  "count": 45,
  "next": "http://localhost:8001/api/notifications/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "user_id": 5,
      "type": "in_app",
      "status": "unread",
      "event": "order_created",
      "title": "New Order Received",
      "message": "You have received a new order from John Doe",
      "data": {
        "order_id": 123,
        "buyer_name": "John Doe"
      },
      "read_at": null,
      "sent_at": "2025-12-04T10:00:00Z",
      "created_at": "2025-12-04T09:59:00Z"
    }
  ]
}
```

#### Получить одно уведомление

```http
GET /api/notifications/{id}/
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "user_id": 5,
  "type": "email",
  "status": "sent",
  "event": "review_received",
  "title": "You received a review",
  "message": "Jane Smith left a 5-star review on your gig 'Web Design'",
  "data": {
    "review_id": 456,
    "rating": 5,
    "gig_title": "Web Design"
  },
  "email_to": "user@example.com",
  "email_subject": "You received a review",
  "sent_at": "2025-12-04T08:00:00Z",
  "read_at": null,
  "created_at": "2025-12-04T07:59:00Z"
}
```

#### Отметить уведомление как прочитанное

```http
POST /api/notifications/{id}/mark-as-read/
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "status": "read",
  "read_at": "2025-12-04T10:05:00Z"
}
```

#### Отметить все уведомления как прочитанные

```http
POST /api/notifications/mark-all-as-read/
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "updated_count": 12,
  "message": "12 notifications marked as read"
}
```

#### Удалить уведомление

```http
DELETE /api/notifications/{id}/
Authorization: Bearer {access_token}
```

**Response (204 No Content)**

#### Удалить все прочитанные уведомления

```http
DELETE /api/notifications/delete-read/
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "deleted_count": 8,
  "message": "8 read notifications deleted"
}
```

#### Получить непрочитанные уведомления

```http
GET /api/notifications/unread/
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "unread_count": 5,
  "notifications": [
    {
      "id": 1,
      "type": "in_app",
      "title": "New Order Received",
      "created_at": "2025-12-04T10:00:00Z"
    }
  ]
}
```

### Предпочтения уведомлений

#### Получить предпочтения уведомлений

```http
GET /api/notification-preferences/
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "user_id": 5,
  "email_enabled": true,
  "in_app_enabled": true,
  "push_enabled": false,
  "order_updates": true,
  "review_updates": true,
  "message_updates": false,
  "created_at": "2025-12-01T10:00:00Z",
  "updated_at": "2025-12-03T15:30:00Z"
}
```

#### Обновить предпочтения уведомлений

```http
PATCH /api/notification-preferences/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "email_enabled": true,
  "in_app_enabled": true,
  "push_enabled": true,
  "order_updates": true,
  "review_updates": false,
  "message_updates": true
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "user_id": 5,
  "email_enabled": true,
  "in_app_enabled": true,
  "push_enabled": true,
  "order_updates": true,
  "review_updates": false,
  "message_updates": true,
  "updated_at": "2025-12-04T10:00:00Z"
}
```

#### Отключить все уведомления

```http
POST /api/notification-preferences/disable-all/
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "message": "All notifications disabled",
  "email_enabled": false,
  "in_app_enabled": false,
  "push_enabled": false
}
```

### Отправка уведомлений (внутренний API)

#### Отправить уведомление

```http
POST /api/notifications/send/
Authorization: Bearer {service_token}
Content-Type: application/json

{
  "user_id": 5,
  "type": "in_app",
  "event": "order_created",
  "title": "New Order",
  "message": "You have received a new order",
  "data": {
    "order_id": 123,
    "amount": 50
  }
}
```

**Response (201 Created):**
```json
{
  "id": 2,
  "user_id": 5,
  "type": "in_app",
  "status": "pending",
  "event": "order_created",
  "title": "New Order",
  "created_at": "2025-12-04T10:00:00Z"
}
```

#### Отправить уведомление на email

```http
POST /api/notifications/send-email/
Authorization: Bearer {service_token}
Content-Type: application/json

{
  "user_id": 5,
  "email_to": "user@example.com",
  "event": "verification",
  "email_subject": "Verify your email",
  "email_template": "verify_email",
  "template_context": {
    "verification_link": "https://example.com/verify?code=abc123",
    "user_name": "John Doe"
  }
}
```

**Response (201 Created):**
```json
{
  "id": 3,
  "user_id": 5,
  "type": "email",
  "status": "pending",
  "email_to": "user@example.com",
  "message": "Notification queued for sending",
  "task_id": "abc123def456"
}
```

#### Отправить push уведомление

```http
POST /api/notifications/send-push/
Authorization: Bearer {service_token}
Content-Type: application/json

{
  "user_id": 5,
  "title": "Order Update",
  "message": "Your order has been delivered",
  "data": {
    "order_id": 123,
    "tracking_url": "https://example.com/track/123"
  }
}
```

**Response (201 Created):**
```json
{
  "id": 4,
  "user_id": 5,
  "type": "push",
  "status": "pending",
  "title": "Order Update",
  "message": "queued for delivery"
}
```

## Celery Tasks

### Асинхронные задачи

#### send_email_notification

Отправляет email уведомление.

```python
from apps.notifications.tasks import send_email_notification

# Вызов задачи
send_email_notification.delay(
    notification_id=1,
    email_to='user@example.com',
    subject='Order Confirmation',
    template_name='order_confirmation',
    context={
        'order_id': 123,
        'order_total': 100,
        'user_name': 'John Doe'
    }
)
```

#### send_in_app_notification

Сохраняет in-app уведомление.

```python
from apps.notifications.tasks import send_in_app_notification

send_in_app_notification.delay(
    user_id=5,
    title='New Message',
    message='You have a new message from John',
    data={'message_id': 456, 'sender_id': 3}
)
```

#### send_push_notification

Отправляет push уведомление на мобильные устройства.

```python
from apps.notifications.tasks import send_push_notification

send_push_notification.delay(
    user_id=5,
    title='Order Delivered',
    message='Your order has been delivered',
    data={'order_id': 123}
)
```

#### process_notification_batch

Обработка пакета уведомлений.

```python
from apps.notifications.tasks import process_notification_batch

notifications = [
    {
        'user_id': 5,
        'type': 'in_app',
        'title': 'Notification 1',
        'message': 'Message 1'
    },
    {
        'user_id': 6,
        'type': 'email',
        'email_to': 'user2@example.com',
        'title': 'Notification 2',
        'message': 'Message 2'
    }
]

process_notification_batch.delay(notifications)
```

## Конфигурация

### Переменные окружения

```bash
# Django
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,notification-service

# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=notification_service_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/2

# Celery
CELERY_BROKER_URL=redis://redis:6379/2
CELERY_RESULT_BACKEND=redis://redis:6379/3
CELERY_ACCEPT_CONTENT=json
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_TIMEZONE=UTC

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@example.com

# Push notifications (Firebase)
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=your-key-id
FIREBASE_PRIVATE_KEY=your-private-key
FIREBASE_CLIENT_EMAIL=your-client-email
FIREBASE_CLIENT_ID=your-client-id
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token

# Services
USER_SERVICE_URL=http://user-service:8000

# Security
SECURE_SSL_REDIRECT=False  # True в production
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://yourapp.com
```

### Django Settings

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'django_celery_beat',
    'apps.notifications',
]

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/2')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/3')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

CELERY_BEAT_SCHEDULE = {
    'cleanup-old-notifications': {
        'task': 'apps.notifications.tasks.cleanup_old_notifications',
        'schedule': crontab(hour=2, minute=0),  # каждый день в 2:00 AM
    },
    'retry-failed-notifications': {
        'task': 'apps.notifications.tasks.retry_failed_notifications',
        'schedule': crontab(minute='*/30'),  # каждые 30 минут
    },
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': os.getenv('POSTGRES_HOST', 'postgres'),
        'PORT': os.getenv('POSTGRES_PORT', 5432),
        'NAME': os.getenv('POSTGRES_DB', 'notification_service_db'),
        'USER': os.getenv('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'postgres'),
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://redis:6379/2'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

## Docker

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh
RUN chmod +x celery_entrypoint.sh

EXPOSE 8001

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8001/api/health/ || exit 1

ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8001", "--workers", "3"]
```

### docker-compose.yml

```yaml
services:
  notification-service:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: notification_service
    restart: unless-stopped
    ports:
      - "8001:8001"
    environment:
      - DEBUG=True
      - SECRET_KEY=dev-secret-key
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_DB=notification_service_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - REDIS_URL=redis://redis:6379/2
      - CELERY_BROKER_URL=redis://redis:6379/2
      - USER_SERVICE_URL=http://user-service:8000
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - microservices_network

  notification-celery-worker:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: notification_celery_worker
    restart: unless-stopped
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings
      - REDIS_URL=redis://redis:6379/2
      - CELERY_BROKER_URL=redis://redis:6379/2
      - POSTGRES_HOST=postgres
      - POSTGRES_DB=notification_service_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    depends_on:
      redis:
        condition: service_healthy
    command: ./celery_entrypoint.sh
    networks:
      - microservices_network

  notification-celery-beat:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: notification_celery_beat
    restart: unless-stopped
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings
      - REDIS_URL=redis://redis:6379/2
      - CELERY_BROKER_URL=redis://redis:6379/2
      - POSTGRES_HOST=postgres
      - POSTGRES_DB=notification_service_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    depends_on:
      redis:
        condition: service_healthy
    command: celery -A config beat -l info
    networks:
      - microservices_network
```

## Примеры использования

### cURL примеры

#### Получить уведомления

```bash
curl -X GET http://localhost:8001/api/notifications/?status=unread \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

#### Отметить как прочитанное

```bash
curl -X POST http://localhost:8001/api/notifications/1/mark-as-read/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

#### Обновить предпочтения

```bash
curl -X PATCH http://localhost:8001/api/notification-preferences/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "email_enabled": true,
    "push_enabled": false,
    "review_updates": true
  }'
```

### Python примеры

```python
import requests
import os

BASE_URL = 'http://localhost:8001'
ACCESS_TOKEN = 'your_access_token'

headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}

# Получить уведомления
response = requests.get(
    f'{BASE_URL}/api/notifications/?status=unread',
    headers=headers
)
notifications = response.json()
print(f"Unread notifications: {notifications['count']}")

# Отметить как прочитанное
notification_id = notifications['results'][0]['id']
response = requests.post(
    f'{BASE_URL}/api/notifications/{notification_id}/mark-as-read/',
    headers=headers
)
print(response.json())

# Получить предпочтения
response = requests.get(
    f'{BASE_URL}/api/notification-preferences/',
    headers=headers
)
prefs = response.json()
print(f"Email enabled: {prefs['email_enabled']}")

# Обновить предпочтения
response = requests.patch(
    f'{BASE_URL}/api/notification-preferences/',
    json={'email_enabled': False, 'push_enabled': True},
    headers=headers
)
print(response.json())
```

### Celery примеры

```python
from celery import shared_task
from apps.notifications.tasks import send_email_notification, send_in_app_notification

# Отправить email уведомление
send_email_notification.delay(
    notification_id=1,
    email_to='user@example.com',
    subject='Order Confirmation',
    template_name='order_confirmation',
    context={
        'order_id': 123,
        'order_total': 100,
        'user_name': 'John'
    }
)

# Отправить in-app уведомление
send_in_app_notification.delay(
    user_id=5,
    title='New Order',
    message='You received a new order!',
    data={'order_id': 123}
)
```

## Тестирование

```bash
# Запуск тестов
python manage.py test apps.notifications

# С покрытием
coverage run --source='apps.notifications' manage.py test
coverage report
coverage html
```

## Безопасность

1. **Email отправки** - используется официальный SMTP сервер
2. **Push уведомления** - подтверждение через Firebase
3. **Rate limiting** - 100 уведомлений на пользователя в час
4. **Шифрование** - все чувствительные данные шифруются

## Производительность

1. **Асинхронная обработка** - использование Celery для фоновых задач
2. **Батч-обработка** - отправка нескольких уведомлений одновременно
3. **Кэширование** - предпочтения уведомлений кэшируются в Redis
4. **Retry механизм** - автоматический повтор при ошибках

## Troubleshooting

```bash
# Проверить Celery worker
docker-compose logs notification-celery-worker

# Проверить Celery tasks
docker-compose exec notification-service celery -A config inspect active

# Очистить Redis кэш
redis-cli -n 2 FLUSHDB
```

## См. также

- [User Service](USER-SERVICE.md)
- [API Gateway Service](API-GATEWAY.md)
- [Архитектура системы](../ARCHITECTURE.md)
