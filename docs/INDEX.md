# Индекс документации

Полный каталог документации для микросервисной платформы.

## Быстрая навигация

### Начало работы
- [README](../README.md) - Общий обзор проекта
- [Быстрый старт](../README.md#быстрый-старт) - Установка и запуск
- [Требования](../README.md#требования) - Системные требования

### Основная документация
- [Архитектура системы](ARCHITECTURE.md) - Детальное описание архитектуры
- [API документация](API.md) - Полная документация API endpoints
- [Развертывание](DEPLOYMENT.md) - Production и development развертывание
- [Разработка](DEVELOPMENT.md) - Руководство для разработчиков

### Документация микросервисов
- [API Gateway](services/API-GATEWAY.md) - Маршрутизация и аутентификация
- [User Service](services/USER-SERVICE.md) - Управление пользователями
- [Notification Service](services/NOTIFICATION-SERVICE.md) - Система уведомлений
- [Freelance Service](services/FREELANCE-SERVICE.md) - Фриланс платформа
- [Content Service](services/CONTENT-SERVICE.md) - Контент и каналы
- [Marketplace Service](services/MARKETPLACE-SERVICE.md) - Маркетплейс товаров

## Структура документации

```
docs/
├── INDEX.md                    # Этот файл
├── ARCHITECTURE.md             # Архитектура системы
├── API.md                      # API документация
├── DEPLOYMENT.md               # Развертывание
├── DEVELOPMENT.md              # Разработка
└── services/                   # Документация сервисов
    ├── API-GATEWAY.md
    ├── USER-SERVICE.md
    ├── NOTIFICATION-SERVICE.md
    ├── FREELANCE-SERVICE.md
    ├── CONTENT-SERVICE.md
    └── MARKETPLACE-SERVICE.md
```

## Архитектура

### Обзор системы

Платформа состоит из 6 микросервисов:

| Сервис | Порт | Назначение | Документация |
|--------|------|-----------|--------------|
| API Gateway | 8080 | Маршрутизация, JWT auth, Rate limiting | [Документация](services/API-GATEWAY.md) |
| User Service | 8000 | Пользователи, профили, аутентификация | [Документация](services/USER-SERVICE.md) |
| Notification Service | 8001 | Email, In-app, Push уведомления | [Документация](services/NOTIFICATION-SERVICE.md) |
| Freelance Service | 8002 | Услуги, заказы, отзывы | [Документация](services/FREELANCE-SERVICE.md) |
| Content Service | 8003 | Каналы, посты, комментарии | [Документация](services/CONTENT-SERVICE.md) |
| Marketplace Service | 8004 | Товары, категории | [Документация](services/MARKETPLACE-SERVICE.md) |

### Базы данных

Каждый сервис имеет изолированную базу данных PostgreSQL:

- `user_service_db` - User Service
- `notification_service_db` - Notification Service
- `freelance_service_db` - Freelance Service
- `content_service_db` - Content Service
- `marketplace_service_db` - Marketplace Service

### Инфраструктура

- **PostgreSQL 16** - Реляционная база данных
- **Redis 7** - Кэширование и очереди
- **Docker** - Контейнеризация
- **Gunicorn** - WSGI сервер
- **Celery** - Асинхронные задачи

Подробнее: [ARCHITECTURE.md](ARCHITECTURE.md)

## API Endpoints

### Базовые URL

```
Production:  https://yourdomain.com/api
Development: http://localhost:8080/api
```

### Основные endpoints

#### Аутентификация
```
POST   /api/auth/login/       # Вход
POST   /api/auth/logout/      # Выход
POST   /api/auth/refresh/     # Обновить токен
POST   /api/auth/verify/      # Проверить токен
GET    /api/auth/me/          # Текущий пользователь
```

#### User Service
```
POST   /api/users/            # Регистрация
GET    /api/profile/          # Получить профиль
PUT    /api/profile/update/   # Обновить профиль
POST   /api/set-role/         # Установить роль
```

#### Notification Service
```
POST   /api/notifications/send/                           # Отправить
GET    /api/notifications/user/{user_id}/                # Получить
POST   /api/notifications/{id}/read/                     # Отметить прочитанным
GET    /api/notifications/preferences/{user_id}/         # Настройки
```

#### Freelance Service
```
GET    /api/gigs/             # Список услуг
POST   /api/gigs/             # Создать услугу
GET    /api/gigs/{id}/        # Детали услуги
POST   /api/orders/           # Создать заказ
GET    /api/orders/           # Список заказов
POST   /api/reviews/          # Создать отзыв
GET    /api/categories/       # Категории
```

#### Content Service
```
GET    /api/channels/         # Список каналов
POST   /api/channels/         # Создать канал
POST   /api/channels/{slug}/posts/  # Создать пост
GET    /api/posts/            # Список постов
POST   /api/likes/            # Добавить лайк
POST   /api/comments/         # Создать комментарий
```

#### Marketplace Service
```
GET    /api/products/         # Список товаров
POST   /api/products/         # Создать товар
GET    /api/products/{id}/    # Детали товара
GET    /api/categories/       # Категории
```

Полная документация: [API.md](API.md)

## Развертывание

### Локальное развертывание

```bash
# 1. Клонировать репозиторий
git clone https://github.com/loowpts/microservice-platform.git
cd microservice-platform

# 2. Настроить .env
cp .env.example .env

# 3. Запустить сервисы
docker-compose up -d

# 4. Применить миграции
docker-compose exec user-service python manage.py migrate
# ... для остальных сервисов

# 5. Создать суперпользователя
docker-compose exec user-service python manage.py createsuperuser
```

### Production развертывание

1. Обновить `.env` с production настройками
2. Настроить SSL сертификаты (Let's Encrypt)
3. Настроить Nginx как reverse proxy
4. Настроить firewall
5. Настроить backup
6. Настроить мониторинг

Подробная инструкция: [DEPLOYMENT.md](DEPLOYMENT.md)

## Разработка

### Настройка окружения

```bash
# Установить Python 3.11+
python --version

# Установить Docker
docker --version

# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Установить зависимости
pip install -r services/user-service/requirements.txt
```

### Создание нового микросервиса

1. Создать структуру Django проекта
2. Настроить Dockerfile
3. Добавить в docker-compose.yml
4. Создать БД в init-databases.sql
5. Добавить маршруты в API Gateway
6. Написать тесты
7. Документировать

Полное руководство: [DEVELOPMENT.md](DEVELOPMENT.md)

## Тестирование

### Запуск тестов

```bash
# Все тесты
docker-compose exec user-service pytest

# С покрытием
docker-compose exec user-service pytest --cov=apps --cov-report=html

# Конкретный файл
docker-compose exec user-service pytest apps/users/tests/test_views.py
```

### Типы тестов

- **Unit тесты** - Тестирование отдельных компонентов
- **Integration тесты** - Тестирование взаимодействия сервисов
- **E2E тесты** - Тестирование полных сценариев

## Мониторинг и логи

### Health Checks

```bash
# Проверка всех сервисов
curl http://localhost:8080/api/health/

# Проверка конкретного сервиса
curl http://localhost:8000/api/health/
```

### Просмотр логов

```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f user-service

# Последние 100 строк
docker-compose logs --tail=100 user-service
```

## Backup и восстановление

### Backup базы данных

```bash
# Все базы
docker-compose exec postgres pg_dumpall -U postgres > backups/full_backup.sql

# Конкретная БД
docker-compose exec postgres pg_dump -U postgres user_service_db > backups/user_service.sql
```

### Восстановление

```bash
cat backups/full_backup.sql | docker-compose exec -T postgres psql -U postgres
```

Подробнее: [DEPLOYMENT.md#backup-и-восстановление](DEPLOYMENT.md#backup-и-восстановление)

## Технологический стек

### Backend
- Django 5.2.5
- Django REST Framework 3.14.0
- Python 3.11

### Databases
- PostgreSQL 16
- Redis 7

### Infrastructure
- Docker & Docker Compose
- Gunicorn 21.2.0
- Celery 5.3.4

### Testing
- pytest 7.4.4
- pytest-django
- factory-boy

### Security
- JWT (PyJWT 2.10.1)
- CORS (django-cors-headers)
- Rate Limiting

## Безопасность

### Checklist

- [ ] DEBUG=False в production
- [ ] Сильные пароли для SECRET_KEY, JWT_SECRET_KEY
- [ ] HTTPS через SSL сертификаты
- [ ] Firewall настроен
- [ ] PostgreSQL и Redis не доступны извне
- [ ] Регулярные backup
- [ ] Rate limiting включен
- [ ] CORS настроен правильно
- [ ] Security headers добавлены

Подробнее: [DEPLOYMENT.md#безопасность-в-production](DEPLOYMENT.md#безопасность-в-production)

## Масштабирование

### Горизонтальное

```bash
# Масштабирование User Service
docker-compose up -d --scale user-service=3
```

### Вертикальное

Настройка resource limits в docker-compose.yml:

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
```

Подробнее: [DEPLOYMENT.md#масштабирование](DEPLOYMENT.md#масштабирование)

## Troubleshooting

### Частые проблемы

**Сервис не запускается:**
```bash
docker-compose logs service-name
docker-compose up -d --build service-name
```

**База данных недоступна:**
```bash
docker-compose exec postgres psql -U postgres
docker-compose logs postgres
```

**Redis недоступен:**
```bash
docker-compose exec redis redis-cli ping
```

Подробнее: [DEPLOYMENT.md#troubleshooting](DEPLOYMENT.md#troubleshooting)

## Вклад в проект

1. Fork репозиторий
2. Создать feature branch
3. Commit изменения
4. Push в branch
5. Создать Pull Request

## Roadmap

- [ ] GraphQL API
- [ ] Kubernetes манифесты
- [ ] Prometheus/Grafana мониторинг
- [ ] ELK stack для логов
- [ ] Service Mesh (Istio)
- [ ] gRPC между сервисами
- [ ] Distributed tracing (Jaeger)

## Контакты

- GitHub: [https://github.com/loowpts/microservice-platform](https://github.com/loowpts/microservice-platform)
- Issues: [GitHub Issues](https://github.com/loowpts/microservice-platform/issues)

## Лицензия

MIT License - см. [LICENSE](../LICENSE)

---

**Последнее обновление:** 2025-12-04

**Версия документации:** 1.0.0
