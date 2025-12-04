# Microservice Platform

> Масштабируемая микросервисная платформа на Django с поддержкой фриланс-услуг, маркетплейса товаров и контент-каналов

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2.5-green.svg)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.14.0-red.svg)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-red.svg)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://www.docker.com/)

## Содержание

- [Обзор](#обзор)
- [Архитектура](#архитектура)
- [Микросервисы](#микросервисы)
- [Технологический стек](#технологический-стек)
- [Быстрый старт](#быстрый-старт)
- [Документация](#документация)
- [API Reference](#api-reference)
- [Разработка](#разработка)
- [Тестирование](#тестирование)
- [Лицензия](#лицензия)

## Обзор

Это полнофункциональная микросервисная платформа, включающая:

- **Фриланс-платформу** для заказа услуг и взаимодействия с исполнителями
- **Маркетплейс** для продажи физических товаров
- **Контент-платформу** с каналами, постами и комментариями
- **Систему уведомлений** с поддержкой email, in-app и push
- **Управление пользователями** с JWT аутентификацией и ролями

### Основные возможности

- Микросервисная архитектура с независимым масштабированием
- API Gateway для маршрутизации запросов
- JWT аутентификация с access/refresh токенами
- Асинхронная обработка задач через Celery
- Real-time уведомления
- Docker контейнеризация
- PostgreSQL для каждого сервиса (Database per Service)
- Redis для кэширования и очередей
- Health checks и мониторинг

## Архитектура

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────┐
│     API Gateway         │
│       :8080            │
└────────┬────────────────┘
         │
    ┌────┴────┬────────┬────────┬────────┐
    ▼         ▼        ▼        ▼        ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ User   │ │Notific.│ │Freelanc│ │Content │ │Marketpl│
│Service │ │Service │ │Service │ │Service │ │Service │
│ :8000  │ │ :8001  │ │ :8002  │ │ :8003  │ │ :8004  │
└───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘
    │          │          │          │          │
    └──────────┴──────────┴──────────┴──────────┘
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
         ┌──────────┐          ┌──────────┐
         │PostgreSQL│          │  Redis   │
         │  :5432   │          │  :6379   │
         └──────────┘          └──────────┘
```

Подробная архитектура: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Микросервисы

### 1. API Gateway (:8080)
Единая точка входа для всех клиентских запросов.

**Функции:**
- Маршрутизация на микросервисы
- JWT аутентификация
- Rate limiting
- Логирование запросов
- CORS управление

**Документация:** [docs/services/API-GATEWAY.md](docs/services/API-GATEWAY.md)

### 2. User Service (:8000)
Управление пользователями и аутентификация.

**Функции:**
- Регистрация и аутентификация
- Управление профилями
- Роли: freelancer, seller, moderator
- JWT токены (access/refresh)

**Документация:** [docs/services/USER-SERVICE.md](docs/services/USER-SERVICE.md)

### 3. Notification Service (:8001)
Централизованная система уведомлений.

**Функции:**
- Email уведомления (Celery)
- In-app уведомления
- Push уведомления
- Настройки уведомлений
- Асинхронная обработка

**Документация:** [docs/services/NOTIFICATION-SERVICE.md](docs/services/NOTIFICATION-SERVICE.md)

### 4. Freelance Service (:8002)
Платформа для фриланс-услуг.

**Функции:**
- Услуги (gigs) с пакетами
- Заказы и доставка
- Отзывы и рейтинги
- Портфолио
- Категории и поиск

**Документация:** [docs/services/FREELANCE-SERVICE.md](docs/services/FREELANCE-SERVICE.md)

### 5. Content Service (:8003)
Платформа контента и каналов.

**Функции:**
- Каналы и посты
- Древовидные комментарии
- Лайки и взаимодействия
- Управление членством
- Роли в каналах

**Документация:** [docs/services/CONTENT-SERVICE.md](docs/services/CONTENT-SERVICE.md)

### 6. Marketplace Service (:8004)
Маркетплейс товаров.

**Функции:**
- Товары с изображениями
- Категории
- Избранное
- Поиск
- Отзывы

**Документация:** [docs/services/MARKETPLACE-SERVICE.md](docs/services/MARKETPLACE-SERVICE.md)

## Технологический стек

### Backend
- **Framework:** Django 5.2.5
- **API:** Django REST Framework 3.14.0
- **Language:** Python 3.11

### Databases & Cache
- **Database:** PostgreSQL 16
- **Cache:** Redis 7
- **Task Queue:** Celery 5.3.4

### Authentication & Security
- **Auth:** JWT (PyJWT 2.10.1)
- **Session:** django-redis

### Infrastructure
- **Containerization:** Docker & Docker Compose
- **Web Server:** Gunicorn 21.2.0
- **WebSockets:** Django Channels 4.0.0

### Development
- **Testing:** pytest, pytest-django, factory-boy
- **Code Quality:** flake8, black
- **API Testing:** httpx, requests

## Быстрый старт

### Требования

- Docker 20.10+
- Docker Compose 2.0+
- Git

### Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/loowpts/microservice-platform.git
cd microservice-platform
```

2. Настройте переменные окружения:
```bash
cp .env.example .env
# Отредактируйте .env файл
```

3. Запустите все сервисы:
```bash
docker-compose up -d
```

4. Выполните миграции:
```bash
docker-compose exec user-service python manage.py migrate
docker-compose exec notification-service python manage.py migrate
docker-compose exec freelance-service python manage.py migrate
docker-compose exec content-service python manage.py migrate
docker-compose exec marketplace-service python manage.py migrate
```

5. Создайте суперпользователя:
```bash
docker-compose exec user-service python manage.py createsuperuser
```

### Проверка работоспособности

Откройте в браузере:
- API Gateway: http://localhost:8080/api/health/
- User Service: http://localhost:8000/api/health/
- Notification Service: http://localhost:8001/api/health/

Все сервисы должны вернуть `{"status": "healthy"}`

## Документация

### Основная документация
- [Архитектура системы](docs/ARCHITECTURE.md)
- [Руководство по развертыванию](docs/DEPLOYMENT.md)
- [API документация](docs/API.md)
- [Разработка](docs/DEVELOPMENT.md)

### Документация по сервисам
- [API Gateway](docs/services/API-GATEWAY.md)
- [User Service](docs/services/USER-SERVICE.md)
- [Notification Service](docs/services/NOTIFICATION-SERVICE.md)
- [Freelance Service](docs/services/FREELANCE-SERVICE.md)
- [Content Service](docs/services/CONTENT-SERVICE.md)
- [Marketplace Service](docs/services/MARKETPLACE-SERVICE.md)

## API Reference

### Базовые URL

| Сервис | Internal URL | External URL (через Gateway) |
|--------|-------------|------------------------------|
| API Gateway | - | http://localhost:8080 |
| User Service | http://user-service:8000 | http://localhost:8080/api/auth, /api/users |
| Notification Service | http://notification-service:8001 | http://localhost:8080/api/notifications |
| Freelance Service | http://freelance-service:8002 | http://localhost:8080/api/gigs, /api/orders |
| Content Service | http://content-service:8003 | http://localhost:8080/api/posts, /api/channels |
| Marketplace Service | http://marketplace-service:8004 | http://localhost:8080/api/products |

### Аутентификация

Все защищенные endpoints требуют JWT токен в header:
```http
Authorization: Bearer <access_token>
```

#### Получение токена
```bash
curl -X POST http://localhost:8080/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

Response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John"
  }
}
```

### Примеры запросов

#### Регистрация пользователя
```bash
curl -X POST http://localhost:8080/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "securepass123",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

#### Получение профиля
```bash
curl http://localhost:8080/api/profile/ \
  -H "Authorization: Bearer <access_token>"
```

#### Создание услуги (gig)
```bash
curl -X POST http://localhost:8080/api/gigs/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Web Design Service",
    "description": "Professional web design",
    "category_id": 1,
    "packages": [
      {
        "type": "basic",
        "price": "50.00",
        "delivery_time": 3
      }
    ]
  }'
```

Полная API документация: [docs/API.md](docs/API.md)

## Разработка

### Структура проекта

```
microservice-platform/
├── services/
│   ├── api-gateway/         # API Gateway
│   ├── user-service/        # User Service
│   ├── notification-service/# Notification Service
│   ├── freelance-service/   # Freelance Service
│   ├── content-service/     # Content Service
│   └── marketplace-service/ # Marketplace Service
├── docs/                    # Документация
├── docker-compose.yml       # Docker Compose конфигурация
├── init-databases.sql       # SQL скрипты инициализации
└── .env                     # Переменные окружения
```

### Локальная разработка

#### Запуск отдельного сервиса
```bash
docker-compose up user-service
```

#### Просмотр логов
```bash
docker-compose logs -f user-service
```

#### Выполнение команд Django
```bash
docker-compose exec user-service python manage.py shell
```

#### Подключение к БД
```bash
docker-compose exec postgres psql -U postgres -d user_service_db
```

### Добавление нового микросервиса

1. Создайте директорию в [services/](services/)
2. Добавьте Django проект
3. Создайте Dockerfile и docker-compose.yml
4. Обновите главный docker-compose.yml
5. Добавьте маршруты в API Gateway
6. Создайте базу данных в init-databases.sql

Подробнее: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)

## Тестирование

### Запуск тестов

```bash
# Все тесты
docker-compose exec user-service pytest

# С покрытием
docker-compose exec user-service pytest --cov=apps --cov-report=html

# Конкретный файл
docker-compose exec user-service pytest apps/users/tests/test_views.py

# С выводом print
docker-compose exec user-service pytest -s
```

### Интеграционные тесты

```bash
# Тестирование взаимодействия сервисов
docker-compose exec freelance-service pytest apps/orders/tests/test_integration.py
```

## CI/CD

Проект использует GitHub Actions для автоматизации:

- Линтинг кода
- Запуск тестов
- Сборка Docker образов
- Деплой (опционально)

См. [.github/workflows/](.github/workflows/)

## Мониторинг

### Health Checks

Каждый сервис предоставляет health check endpoint:

```bash
# Проверка всех сервисов через Gateway
curl http://localhost:8080/api/health/

# Проверка конкретного сервиса
curl http://localhost:8000/api/health/
```

### Метрики

- **Response time:** Время ответа сервиса
- **Status:** Статус сервиса (healthy/unhealthy)
- **Database:** Подключение к БД
- **Redis:** Подключение к Redis

## Производственное развертывание

### Подготовка

1. Обновите `.env` с production настройками
2. Установите `DEBUG=False`
3. Используйте сильные пароли для БД и Redis
4. Настройте HTTPS через Nginx/Traefik
5. Настройте backup для БД

### Развертывание

```bash
# Production режим
docker-compose -f docker-compose.prod.yml up -d
```

Подробная инструкция: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

## Безопасность

- JWT токены с коротким временем жизни
- HTTPS для всех соединений (рекомендуется)
- Rate limiting в API Gateway
- CORS настройки
- SQL injection защита через ORM
- XSS защита в Django
- Изолированные Docker сети
- Отдельные БД для каждого сервиса

## Производительность

- Redis кэширование
- Database connection pooling
- Gunicorn workers (3 per service)
- Асинхронные задачи через Celery
- Database indexing
- Оптимизированные SQL запросы

## Масштабирование

### Горизонтальное

```bash
# Масштабирование User Service до 3 реплик
docker-compose up -d --scale user-service=3

# Потребуется load balancer (Nginx/HAProxy)
```

### Вертикальное

Настройка ресурсов в docker-compose.yml:

```yaml
user-service:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 2G
```

## Известные проблемы

- WebSocket поддержка требует дополнительной настройки
- Push уведомления требуют настройки Firebase/OneSignal

## Roadmap

- [ ] GraphQL API поддержка
- [ ] Kubernetes манифесты
- [ ] Monitoring stack (Prometheus/Grafana)
- [ ] ELK stack для логов
- [ ] Service Mesh (Istio)
- [ ] gRPC между сервисами
- [ ] API rate limiting per user
- [ ] Distributed tracing (Jaeger)
- [ ] 
---

Made with ❤️ by lee
