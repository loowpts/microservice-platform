# User Service

## Обзор

User Service отвечает за управление пользователями, аутентификацию, авторизацию и профили пользователей в микросервисной платформе. Сервис обрабатывает регистрацию, вход, управление ролями и данными профилей.

## Основная информация

- **Порт:** 8000
- **Framework:** Django 5.2.5 + DRF 3.14.0
- **Язык:** Python 3.11
- **Database:** PostgreSQL
- **Cache:** Redis
- **Аутентификация:** JWT токены

## Архитектура

```
┌─────────────────────────────────┐
│      User Service :8000         │
├─────────────────────────────────┤
│  Apps:                          │
│  - users (основной)             │
│                                 │
│  Models:                        │
│  - User (CustomUser)            │
│  - UserProfile                  │
│                                 │
│  Endpoints:                     │
│  - /api/auth/                   │
│  - /api/users/                  │
│  - /api/profile/                │
└────────────┬────────────────────┘
             │
             ▼
        PostgreSQL (user_service_db)
        Redis (cache)
```

## Структура проекта

```
user-service/
├── apps/
│   ├── users/
│   │   ├── __init__.py
│   │   ├── models.py           # User, UserProfile
│   │   ├── api.py              # API интеграция
│   │   ├── forms.py            # Django Forms
│   │   ├── admin.py            # Admin интерфейс
│   │   ├── apps.py
│   │   ├── signals.py          # Django сигналы
│   │   ├── tests.py            # Unit тесты
│   │   └── tests/
│   │       └── test_views.py
│   └── __init__.py
├── config/
│   ├── __init__.py
│   ├── settings.py             # Django настройки
│   ├── urls.py                 # URL маршруты
│   ├── wsgi.py
│   └── asgi.py
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── manage.py
├── requirements.txt
└── logging_config.py
```

## Модели данных

### User (CustomUser)

Основная модель пользователя, расширяет Django AbstractBaseUser.

| Поле | Тип | Описание |
|------|-----|---------|
| id | Integer | Первичный ключ (auto-increment) |
| email | EmailField | Уникальный email пользователя |
| first_name | CharField | Имя пользователя |
| last_name | CharField | Фамилия пользователя |
| password | CharField | Захешированный пароль |
| is_active | Boolean | Активен ли аккаунт (default: True) |
| is_staff | Boolean | Является ли staff (default: False) |
| is_verified | Boolean | Верифицирован ли email (default: False) |
| is_freelancer | Boolean | Имеет ли роль фрилансера (default: False) |
| is_seller | Boolean | Имеет ли роль продавца (default: False) |
| is_moderator | Boolean | Является ли модератором (default: False) |
| is_superuser | Boolean | Является ли супер-пользователем (default: False) |
| date_joined | DateTime | Дата регистрации |
| updated_at | DateTime | Дата последнего обновления |
| groups | ManyToMany | Группы разрешений Django |
| user_permissions | ManyToMany | Разрешения Django |

**Методы:**
- `full_name()` - возвращает полное имя пользователя
- `get_full_name()` - Django метод
- `get_short_name()` - Django метод
- `has_perm(perm)` - проверка разрешения
- `has_module_perms(module)` - проверка разрешения модуля

**Индексы:**
- email (unique, indexed)
- date_joined

### UserProfile

Расширенный профиль пользователя, связанный One-to-One с User.

| Поле | Тип | Описание |
|------|-----|---------|
| id | Integer | Первичный ключ |
| user | OneToOneField | Связь с User (on_delete: CASCADE) |
| avatar | ImageField | Аватар пользователя (uploads/avatars/) |
| bio | TextField | Биография (макс. 1000 символов) |
| is_public | Boolean | Публичный ли профиль (default: True) |
| timezone | CharField | Часовой пояс пользователя |
| streak_visibility | Boolean | Видимость streak (default: True) |

**Методы:**
- `role_display()` - возвращает роль(и) пользователя в виде строки
- `get_roles()` - возвращает список ролей

**Связи:**
- `user.profile` - получить профиль пользователя

## API Endpoints

### Аутентификация

#### Регистрация пользователя

```http
POST /api/auth/register/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password_123",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "is_active": true,
    "is_verified": false,
    "roles": ["User"]
  }
}
```

**Ошибки:**
- `400 Bad Request` - validation error (email уже существует, слабый пароль)
- `422 Unprocessable Entity` - missing required fields

#### Вход в аккаунт

```http
POST /api/auth/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password_123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "is_verified": false,
    "roles": ["User", "Freelancer"]
  }
}
```

**Ошибки:**
- `401 Unauthorized` - invalid credentials
- `404 Not Found` - пользователь не найден

#### Обновление токена

```http
POST /api/auth/refresh/
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Выход из аккаунта

```http
POST /api/auth/logout/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Response (200 OK):**
```json
{
  "message": "Successfully logged out"
}
```

### Управление пользователями

#### Получить все пользователей

```http
GET /api/users/?page=1&page_size=20&search=john&role=freelancer
Authorization: Bearer {access_token}
```

**Query Parameters:**
- `page` (int) - номер страницы (default: 1)
- `page_size` (int) - количество результатов на странице (default: 20)
- `search` (string) - поиск по email или имени
- `role` (string) - фильтр по роли (freelancer, seller, moderator, admin)
- `is_verified` (boolean) - фильтр по верификации

**Response (200 OK):**
```json
{
  "count": 150,
  "next": "http://localhost:8000/api/users/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "is_active": true,
      "is_verified": true,
      "roles": ["Freelancer"],
      "date_joined": "2025-12-01T10:00:00Z"
    }
  ]
}
```

#### Создать пользователя (для admins)

```http
POST /api/users/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password": "secure_password_123",
  "first_name": "Jane",
  "last_name": "Smith",
  "is_freelancer": true,
  "is_seller": false
}
```

**Response (201 Created):**
```json
{
  "id": 2,
  "email": "newuser@example.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "is_active": true,
  "is_verified": false,
  "is_freelancer": true,
  "is_seller": false,
  "roles": ["Freelancer"]
}
```

#### Получить пользователя по ID

```http
GET /api/users/{id}/
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_active": true,
  "is_verified": true,
  "is_freelancer": true,
  "is_seller": false,
  "is_moderator": false,
  "roles": ["Freelancer"],
  "date_joined": "2025-12-01T10:00:00Z",
  "updated_at": "2025-12-03T15:30:00Z"
}
```

#### Обновить пользователя

```http
PATCH /api/users/{id}/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "first_name": "Jonathan",
  "last_name": "Doe",
  "is_freelancer": true,
  "is_seller": true
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "Jonathan",
  "last_name": "Doe",
  "is_active": true,
  "is_verified": true,
  "is_freelancer": true,
  "is_seller": true,
  "roles": ["Freelancer", "Seller"],
  "updated_at": "2025-12-04T10:00:00Z"
}
```

#### Удалить пользователя

```http
DELETE /api/users/{id}/
Authorization: Bearer {access_token}
```

**Response (204 No Content)**

### Управление профилями

#### Получить профиль текущего пользователя

```http
GET /api/profile/me/
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "avatar": "https://api.example.com/media/avatars/user1.jpg",
  "bio": "Professional freelancer with 5+ years experience",
  "is_public": true,
  "timezone": "Europe/Moscow",
  "streak_visibility": true,
  "roles": ["Freelancer"]
}
```

#### Получить профиль пользователя по ID

```http
GET /api/profile/{user_id}/
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "avatar": "https://api.example.com/media/avatars/user1.jpg",
  "bio": "Professional freelancer with 5+ years experience",
  "is_public": true,
  "timezone": "Europe/Moscow",
  "roles": ["Freelancer"]
}
```

#### Обновить профиль

```http
PATCH /api/profile/me/
Authorization: Bearer {access_token}
Content-Type: multipart/form-data

{
  "bio": "Updated bio",
  "is_public": true,
  "timezone": "America/New_York",
  "avatar": <binary_file>
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "avatar": "https://api.example.com/media/avatars/user1_new.jpg",
  "bio": "Updated bio",
  "is_public": true,
  "timezone": "America/New_York",
  "roles": ["Freelancer"]
}
```

### Управление ролями

#### Получить роли пользователя

```http
GET /api/users/{id}/roles/
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "roles": ["Freelancer", "Seller"],
  "permissions": [
    "create_gig",
    "create_product",
    "view_analytics",
    "receive_orders"
  ]
}
```

#### Добавить роль пользователю (только админ)

```http
POST /api/users/{id}/roles/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "role": "moderator"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "roles": ["Freelancer", "Seller", "Moderator"],
  "permissions": [
    "create_gig",
    "create_product",
    "view_analytics",
    "receive_orders",
    "moderate_content",
    "manage_disputes"
  ]
}
```

#### Удалить роль пользователя (только админ)

```http
DELETE /api/users/{id}/roles/{role_name}/
Authorization: Bearer {access_token}
```

**Response (204 No Content)**

### Верификация email

#### Отправить код верификации

```http
POST /api/auth/send-verification/
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "message": "Verification email sent",
  "email": "user@example.com"
}
```

#### Проверить код верификации

```http
POST /api/auth/verify-email/
Content-Type: application/json

{
  "email": "user@example.com",
  "code": "123456"
}
```

**Response (200 OK):**
```json
{
  "message": "Email verified successfully",
  "is_verified": true
}
```

## Конфигурация

### Переменные окружения

```bash
# Django
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,user-service

# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=user_service_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/1

# JWT
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_DELTA=3600  # 1 час в секундах
JWT_REFRESH_EXPIRATION_DELTA=604800  # 7 дней в секундах

# Email (для верификации)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Services
NOTIFICATION_SERVICE_URL=http://notification-service:8001

# Security
SECURE_SSL_REDIRECT=False  # True в production
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://yourapp.com
```

### Django Settings (config/settings.py)

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
    'apps.users',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

AUTH_USER_MODEL = 'users.User'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': os.getenv('POSTGRES_HOST', 'postgres'),
        'PORT': os.getenv('POSTGRES_PORT', 5432),
        'NAME': os.getenv('POSTGRES_DB', 'user_service_db'),
        'USER': os.getenv('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'postgres'),
        'CONN_MAX_AGE': 600,
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://redis:6379/1'),
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

# Установка зависимостей системы
RUN apt-get update && apt-get install -y \
    build-essential \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Установка зависимостей Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование приложения
COPY . .

# Создание статических файлов
RUN mkdir -p /app/staticfiles /app/media

# Разрешение скрипта входа
RUN chmod +x entrypoint.sh

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/ || exit 1

ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
```

### docker-compose.yml (для локального запуска)

```yaml
services:
  user-service:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: user_service
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - DEBUG=True
      - SECRET_KEY=dev-secret-key
      - JWT_SECRET_KEY=dev-jwt-secret
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_DB=user_service_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_URL=redis://redis:6379/1
      - NOTIFICATION_SERVICE_URL=http://notification-service:8001
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./:/app
      - user_media:/app/media
    networks:
      - microservices_network

  postgres:
    image: postgres:16-alpine
    container_name: user_postgres
    restart: unless-stopped
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=user_service_db
    volumes:
      - user_postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - microservices_network

  redis:
    image: redis:7-alpine
    container_name: user_redis
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - user_redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - microservices_network

volumes:
  user_postgres_data:
  user_redis_data:
  user_media:

networks:
  microservices_network:
    driver: bridge
```

## Примеры использования

### cURL примеры

#### Регистрация

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

#### Вход

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

#### Получить профиль

```bash
curl -X GET http://localhost:8000/api/profile/me/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

#### Обновить профиль с аватаром

```bash
curl -X PATCH http://localhost:8000/api/profile/me/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -F "bio=My new bio" \
  -F "avatar=@/path/to/avatar.jpg"
```

### Python примеры

```python
import requests
import json

BASE_URL = 'http://localhost:8000'
EMAIL = 'user@example.com'
PASSWORD = 'SecurePass123!'

# Регистрация
register_data = {
    'email': EMAIL,
    'password': PASSWORD,
    'first_name': 'John',
    'last_name': 'Doe'
}
response = requests.post(f'{BASE_URL}/api/auth/register/', json=register_data)
print(response.json())

# Вход
login_data = {
    'email': EMAIL,
    'password': PASSWORD
}
response = requests.post(f'{BASE_URL}/api/auth/login/', json=login_data)
tokens = response.json()
access_token = tokens['access_token']

# Получить профиль
headers = {'Authorization': f'Bearer {access_token}'}
response = requests.get(f'{BASE_URL}/api/profile/me/', headers=headers)
profile = response.json()
print(f"Profile: {profile}")

# Обновить профиль
profile_data = {
    'bio': 'Updated bio',
    'timezone': 'Europe/Moscow'
}
response = requests.patch(
    f'{BASE_URL}/api/profile/me/',
    json=profile_data,
    headers=headers
)
print(response.json())

# Получить все пользователей
response = requests.get(
    f'{BASE_URL}/api/users/?search=john&role=freelancer',
    headers=headers
)
users = response.json()
print(f"Found users: {users['count']}")
```

### JavaScript примеры

```javascript
const BASE_URL = 'http://localhost:8000';
const EMAIL = 'user@example.com';
const PASSWORD = 'SecurePass123!';

// Регистрация
async function register() {
  const response = await fetch(`${BASE_URL}/api/auth/register/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: EMAIL,
      password: PASSWORD,
      first_name: 'John',
      last_name: 'Doe'
    })
  });
  return await response.json();
}

// Вход
async function login() {
  const response = await fetch(`${BASE_URL}/api/auth/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: EMAIL,
      password: PASSWORD
    })
  });
  return await response.json();
}

// Получить профиль
async function getProfile(accessToken) {
  const response = await fetch(`${BASE_URL}/api/profile/me/`, {
    method: 'GET',
    headers: { 'Authorization': `Bearer ${accessToken}` }
  });
  return await response.json();
}

// Обновить профиль
async function updateProfile(accessToken, bio, timezone) {
  const response = await fetch(`${BASE_URL}/api/profile/me/`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      bio,
      timezone
    })
  });
  return await response.json();
}

// Использование
(async () => {
  const registerResult = await register();
  console.log('Register result:', registerResult);

  const loginResult = await login();
  const { access_token } = loginResult;

  const profile = await getProfile(access_token);
  console.log('Profile:', profile);

  const updated = await updateProfile(
    access_token,
    'Updated bio',
    'Europe/Moscow'
  );
  console.log('Updated profile:', updated);
})();
```

## Безопасность

### Best Practices

1. **Пароли**
   - Минимум 8 символов
   - Требует цифр и спецсимволов
   - Хешируются с помощью PBKDF2

2. **JWT токены**
   - Access Token: 1 час (3600 сек)
   - Refresh Token: 7 дней (604800 сек)
   - Хранятся в httpOnly cookies или localStorage

3. **Rate Limiting**
   - Login: 5 попыток в 15 минут
   - Register: 3 попытки в 1 час
   - API общий лимит: 1000 запросов в минуту

4. **Email верификация**
   - Отправляется при регистрации
   - Требуется для получения некоторых функций
   - Код действует 24 часа

## Производительность

### Оптимизации

1. **Database queries**
   - Индексы на email, date_joined
   - select_related для профилей
   - Pagination с page size = 20 по умолчанию

2. **Caching**
   - Redis для кэширования профилей (TTL: 1 час)
   - Кэширование ролей пользователя

3. **Connection pooling**
   - PostgreSQL CONN_MAX_AGE: 600 сек
   - Переиспользование соединений

## Ошибки и их обработка

```python
# Возможные ошибки

# 400 Bad Request
{
  "email": ["This field may not be blank."],
  "password": ["Password is too weak"]
}

# 401 Unauthorized
{
  "error": "Invalid credentials",
  "detail": "No active account found with the given credentials"
}

# 403 Forbidden
{
  "error": "You don't have permission to perform this action"
}

# 404 Not Found
{
  "error": "User not found"
}

# 429 Too Many Requests
{
  "error": "Request throttled. Retry after 5 minutes"
}

# 500 Internal Server Error
{
  "error": "Internal server error",
  "detail": "An unexpected error occurred"
}
```

## Тестирование

### Unit тесты

```bash
# Запуск всех тестов
python manage.py test apps.users

# Запуск конкретного теста
python manage.py test apps.users.tests.test_views.UserRegistrationTest

# С покрытием
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Integration тесты

```bash
# Запуск через pytest
pytest apps/users/tests/test_views.py -v

# С маркерами
pytest -m integration
```

## Локальный запуск

```bash
# Установка зависимостей
pip install -r requirements.txt

# Миграции БД
python manage.py migrate

# Создание супер-пользователя
python manage.py createsuperuser --email admin@example.com

# Запуск сервера
python manage.py runserver 8000

# Или через Gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --reload
```

## Troubleshooting

### Частые проблемы

**1. "FATAL: role \"postgres\" does not exist"**
```bash
# Создать роль в PostgreSQL
docker-compose exec postgres createuser -U postgres -P postgres
```

**2. "ConnectionRefusedError: Connection refused"**
```bash
# Проверить статус сервисов
docker-compose ps

# Проверить logs
docker-compose logs user-service
```

**3. JWT токен не работает**
```bash
# Убедиться что JWT_SECRET_KEY одинаковый
docker-compose exec user-service env | grep JWT_SECRET_KEY
docker-compose exec api-gateway env | grep JWT_SECRET_KEY
```

## Roadmap

- [ ] OAuth2 интеграция (Google, Facebook)
- [ ] Two-factor authentication (2FA)
- [ ] Social login
- [ ] Advanced user preferences
- [ ] User activity logging
- [ ] Account recovery flow
- [ ] Batch user operations
- [ ] LDAP integration

## См. также

- [API Gateway Service](API-GATEWAY.md)
- [Архитектура системы](../ARCHITECTURE.md)
- [REST API документация](../API.md)
