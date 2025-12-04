# Документация Микросервисов

Полная документация для всех микросервисов платформы с подробным описанием API, моделей данных, конфигурации и примерами использования.

## Содержание

### 1. [API Gateway Service](API-GATEWAY.md) - Порт 8080
Единая точка входа для всех клиентских запросов. Отвечает за:
- **Маршрутизация** запросов к микросервисам
- **Аутентификация** через JWT токены
- **Rate limiting** для защиты от перегрузки
- **Логирование** всех запросов
- **Health checks** статуса всех сервисов

**Основные компоненты:**
- Middleware Stack (CORS, JWT, Rate Limiting)
- Router (URL Pattern Matching, Service Discovery)
- Proxy Handler (Request/Response Forwarding)

**Основные технологии:** Django 5.2.5, DRF 3.14.0, Redis

---

### 2. [User Service](USER-SERVICE.md) - Порт 8000
Управление пользователями, аутентификацией и профилями.

**Основные функции:**
- Регистрация и аутентификация пользователей
- JWT токены (access + refresh)
- Управление профилями пользователей
- Система ролей (User, Freelancer, Seller, Moderator, Admin)
- Email верификация

**Модели:**
- `User` - основная модель пользователя
- `UserProfile` - расширенный профиль с аватаром, био, временной зоной

**API Endpoints:**
- `POST /api/auth/register/` - регистрация
- `POST /api/auth/login/` - вход
- `POST /api/auth/refresh/` - обновление токена
- `GET /api/users/` - список пользователей
- `GET /api/profile/me/` - профиль текущего пользователя
- `PATCH /api/profile/me/` - обновление профиля

**Основные технологии:** Django 5.2.5, DRF 3.14.0, PostgreSQL, Redis, JWT

---

### 3. [Notification Service](NOTIFICATION-SERVICE.md) - Порт 8001
Управление уведомлениями с поддержкой множественных каналов.

**Основные функции:**
- Отправка уведомлений (Email, In-App, Push)
- Управление предпочтениями уведомлений
- Асинхронная обработка через Celery
- Автоматический retry при ошибках
- Планирование задач через Celery Beat

**Модели:**
- `Notification` - основная модель уведомления
- `NotificationPreference` - предпочтения пользователя

**API Endpoints:**
- `GET /api/notifications/` - список уведомлений
- `POST /api/notifications/{id}/mark-as-read/` - отметить как прочитанное
- `GET /api/notification-preferences/` - предпочтения
- `PATCH /api/notification-preferences/` - обновление предпочтений
- `POST /api/notifications/send/` - отправить уведомление

**Основные технологии:** Django 5.2.5, DRF 3.14.0, PostgreSQL, Celery, Redis

---

### 4. [Freelance Service](FREELANCE-SERVICE.md) - Порт 8002
Полная платформа для фрилансеров с управлением услугами, заказами и отзывами.

**Основные функции:**
- Создание и управление услугами (gigs)
- Система заказов с различными статусами
- Управление доставкой результатов
- Система отзывов и рейтингов
- Портфолио фрилансеров
- Предложения (proposals) и избранное
- Аналитика продаж

**Модели:**
- `Gig` - услуга с пакетами
- `GigPackage` - пакет услуги (Basic, Standard, Premium)
- `Order` - заказ услуги
- `OrderDelivery` - доставка результата
- `Review` - отзыв о услуге
- `Dispute` - спор между сторонами
- `Portfolio` - портфолио работ
- `Favorite` - избранные услуги

**API Endpoints:**
- `GET /api/gigs/` - поиск услуг
- `POST /api/gigs/` - создать услугу
- `POST /api/orders/` - создать заказ
- `GET /api/reviews/` - получить отзывы
- `GET /api/favorites/` - избранное
- `GET /api/analytics/seller-stats/` - статистика продавца

**Apps:** gigs, orders, reviews, categories, portfolio, proposals, favorites, analytics, search

**Основные технологии:** Django 5.2.5, DRF 3.14.0, PostgreSQL, Redis

---

### 5. [Content Service](CONTENT-SERVICE.md) - Порт 8003
Социальный контент платформы: каналы, посты и комментарии.

**Основные функции:**
- Создание и управление каналами (community)
- Управление членством в каналах с ролями
- Публикация постов с изображениями
- Комментарии и ответы на комментарии
- Лайки и закладки
- Система ролей в канале (Owner, Admin, Moderator, Member)

**Модели:**
- `Channel` - канал/сообщество
- `ChannelMember` - член канала с ролью
- `Post` - пост с метриками (views, likes, comments)
- `Comment` - комментарий с поддержкой вложенности
- `Like` / `Interaction` - лайки и закладки

**API Endpoints:**
- `GET /api/channels/` - список каналов
- `POST /api/channels/` - создать канал
- `POST /api/channels/{id}/join/` - присоединиться
- `GET /api/channels/{id}/posts/` - посты канала
- `POST /api/channels/{id}/posts/` - создать пост
- `POST /api/posts/{id}/like/` - лайкнуть пост
- `POST /api/posts/{id}/comments/` - добавить комментарий

**Apps:** content, posts, comments, interactions, memberships

**Основные технологии:** Django 5.2.5, DRF 3.14.0, PostgreSQL

---

### 6. [Marketplace Service](MARKETPLACE-SERVICE.md) - Порт 8004
Электронная коммерция: товары, категории, поиск и заказы.

**Основные функции:**
- Каталог товаров с фильтрацией
- Система категорий (иерархическая)
- Полнотекстовый поиск товаров
- Управление изображениями товаров
- Система заказов
- Отзывы и рейтинги товаров
- Избранные товары
- Различные условия товаров (new, used, refurbished)

**Модели:**
- `Product` - товар с категорией
- `ProductImage` - изображения товара
- `Category` - категория товаров (с поддержкой подкатегорий)
- `Order` - заказ товаров
- `OrderItem` - товар в заказе
- `Review` - отзыв о товаре
- `Favorite` - избранные товары

**API Endpoints:**
- `GET /api/products/` - поиск и фильтрация товаров
- `POST /api/products/` - создать товар
- `GET /api/categories/` - список категорий
- `POST /api/orders/` - создать заказ
- `GET /api/reviews/` - отзывы товара
- `POST /api/favorites/` - добавить в избранное
- `GET /api/search/` - полнотекстовый поиск

**Apps:** products, categories, orders, reviews, favorites, search

**Основные технологии:** Django 5.2.5, DRF 3.14.0, PostgreSQL, Redis, Elasticsearch

---

## Быстрый старт

### Локальный запуск с Docker Compose

```bash
# Клонировать репозиторий
git clone <repository>
cd microservice-platform

# Установить переменные окружения
cp .env.example .env

# Запустить все сервисы
docker-compose up -d

# Применить миграции
docker-compose exec user-service python manage.py migrate
docker-compose exec notification-service python manage.py migrate
docker-compose exec freelance-service python manage.py migrate
docker-compose exec content-service python manage.py migrate
docker-compose exec marketplace-service python manage.py migrate

# Создать суперпользователя
docker-compose exec user-service python manage.py createsuperuser
```

### Проверка статуса сервисов

```bash
# Health check
curl http://localhost:8080/api/health/

# API Gateway - /api/*
curl http://localhost:8080/api/users/

# Прямые обращения к сервисам
curl http://localhost:8000/api/users/           # User Service
curl http://localhost:8001/api/notifications/   # Notification Service
curl http://localhost:8002/api/gigs/            # Freelance Service
curl http://localhost:8003/api/channels/        # Content Service
curl http://localhost:8004/api/products/        # Marketplace Service
```

## Архитектура

```
┌─────────────┐
│   Клиент    │
│  (Frontend) │
└──────┬──────┘
       │
       ▼
┌──────────────────────┐
│   API Gateway :8080  │
│  (маршрутизация)     │
└─┬──┬──┬──┬───────────┘
  │  │  │  │
  ▼  ▼  ▼  ▼
┌─────────────────────────────────────┐
│  Микросервисы:                      │
│  ┌────────────────────────────────┐ │
│  │ User Service :8000             │ │
│  │ • Аутентификация              │ │
│  │ • Управление пользователями   │ │
│  └────────────────────────────────┘ │
│  ┌────────────────────────────────┐ │
│  │ Notification Service :8001     │ │
│  │ • Email/Push/In-App            │ │
│  │ • Celery асинхронность         │ │
│  └────────────────────────────────┘ │
│  ┌────────────────────────────────┐ │
│  │ Freelance Service :8002        │ │
│  │ • Gigs/Orders/Reviews          │ │
│  │ • Портфолио                    │ │
│  └────────────────────────────────┘ │
│  ┌────────────────────────────────┐ │
│  │ Content Service :8003          │ │
│  │ • Каналы/Посты/Комментарии    │ │
│  └────────────────────────────────┘ │
│  ┌────────────────────────────────┐ │
│  │ Marketplace Service :8004      │ │
│  │ • Товары/Категории/Заказы     │ │
│  └────────────────────────────────┘ │
└─────────────────────────────────────┘
         │
         ▼
    ┌─────────────┐
    │ PostgreSQL  │ (5 баз данных)
    │ Redis       │ (кэш + сессии)
    │ Celery      │ (задачи)
    └─────────────┘
```

## Общие характеристики

### Все сервисы используют:

| Компонент | Версия | Использование |
|-----------|--------|---------------|
| Python | 3.11 | Runtime |
| Django | 5.2.5 | Framework |
| DRF | 3.14.0 | REST API |
| PostgreSQL | 16 | Database |
| Redis | 7 | Cache, Sessions |
| Celery | - | Task Queue (только Notification) |
| Docker | - | Containerization |

### Стандартная конфигурация:

- **Аутентификация:** JWT токены
- **Пагинация:** 20 элементов по умолчанию
- **Rate Limiting:** 1000 запросов/минута
- **CORS:** Настроено для localhost:3000
- **Логирование:** Структурированное логирование

## Процесс разработки

### Для добавления нового API endpoint:

1. **Создать модель** в `apps/<app_name>/models.py`
2. **Создать сериализатор** в `apps/<app_name>/serializers.py`
3. **Создать view** в `apps/<app_name>/views.py`
4. **Добавить URL** в `apps/<app_name>/urls.py`
5. **Написать тесты** в `apps/<app_name>/tests.py`
6. **Обновить миграции** `python manage.py makemigrations`

### Для добавления нового микросервиса:

1. **Создать структуру** как в других сервисах
2. **Добавить в docker-compose.yml**
3. **Добавить маршрутизацию** в API Gateway
4. **Создать документацию**

## Тестирование

```bash
# Unit тесты
python manage.py test apps.<app_name>

# Integration тесты
pytest apps/<app_name>/tests/

# С покрытием
coverage run --source='.' manage.py test
coverage report
coverage html
```

## Деплой

### Production режим

```bash
# Установить переменные окружения
export DEBUG=False
export SECURE_SSL_REDIRECT=True

# Собрать статические файлы
python manage.py collectstatic --noinput

# Применить миграции
python manage.py migrate

# Запустить через Gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### Масштабирование

```bash
# Запустить несколько инстансов
docker-compose up -d --scale user-service=3

# Nginx load balancing
# Конфигурация в nginx.conf
```

## Мониторинг

- **Logs:** `docker-compose logs -f <service>`
- **Metrics:** Prometheus интеграция
- **Health Checks:** `/api/health/` endpoint
- **Performance:** New Relic / DataDog

## Безопасность

- **Аутентификация:** JWT с expiration
- **HTTPS:** Обязательно в production
- **CORS:** Ограничено в production
- **Rate Limiting:** Включено на всех сервисах
- **SQL Injection:** ORM защита
- **XSS:** DRF встроенная защита

## Справка по документации

Каждый файл документации содержит:
- Обзор сервиса
- Основная информация (порт, технологии)
- Архитектура
- Структура проекта
- Полное описание моделей данных
- API Endpoints с примерами запросов/ответов
- Конфигурация и переменные окружения
- Docker setup
- Примеры использования (cURL, Python, JavaScript)
- Безопасность и производительность
- Troubleshooting
- Roadmap и будущие улучшения

## Быстрые ссылки

- [API Gateway](API-GATEWAY.md) - Главная точка входа
- [User Service](USER-SERVICE.md) - Аутентификация и профили
- [Notification Service](NOTIFICATION-SERVICE.md) - Уведомления
- [Freelance Service](FREELANCE-SERVICE.md) - Фриланс платформа
- [Content Service](CONTENT-SERVICE.md) - Социальный контент
- [Marketplace Service](MARKETPLACE-SERVICE.md) - E-commerce

## Контрибьютинг

При создании новых сервисов или обновлении документации:
1. Следовать структуре существующей документации
2. Включать примеры кода
3. Добавлять информацию о безопасности
4. Документировать все API endpoints
5. Обновлять этот INDEX.md

## Контакты и поддержка

- **Documentation:** см. файлы markdown в этой папке
- **Issues:** GitHub issues
- **Development:** Docker environment

---

**Последнее обновление:** 2025-12-04
**Версия документации:** 1.0
**Совместимость:** Python 3.11+, Django 5.2.5+
