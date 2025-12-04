# Документация микросервисной платформы

Добро пожаловать в документацию! Здесь вы найдете всю необходимую информацию для работы с платформой.

## Начало работы

**Новичок в проекте?** Начните отсюда:

1. [Главный README](../README.md) - Обзор проекта и быстрый старт
2. [Архитектура](ARCHITECTURE.md) - Как устроена система
3. [API документация](API.md) - Как работать с API
4. [Развертывание](DEPLOYMENT.md) - Как развернуть проект

## Навигация по документации

### Основные документы

| Документ | Описание | Для кого |
|----------|----------|----------|
| [INDEX.md](INDEX.md) | Полный индекс документации | Все |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Архитектура и компоненты системы | Разработчики, Архитекторы |
| [API.md](API.md) | Полная документация API endpoints | Frontend разработчики, QA |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Развертывание и конфигурация | DevOps, System Admins |
| [DEVELOPMENT.md](DEVELOPMENT.md) | Руководство для разработчиков | Backend разработчики |

### Документация микросервисов

| Сервис | Порт | Документация | Назначение |
|--------|------|--------------|------------|
| API Gateway | 8080 | [API-GATEWAY.md](services/API-GATEWAY.md) | Маршрутизация, аутентификация |
| User Service | 8000 | [USER-SERVICE.md](services/USER-SERVICE.md) | Пользователи, профили |
| Notification Service | 8001 | [NOTIFICATION-SERVICE.md](services/NOTIFICATION-SERVICE.md) | Уведомления |
| Freelance Service | 8002 | [FREELANCE-SERVICE.md](services/FREELANCE-SERVICE.md) | Фриланс услуги |
| Content Service | 8003 | [CONTENT-SERVICE.md](services/CONTENT-SERVICE.md) | Контент, каналы |
| Marketplace Service | 8004 | [MARKETPLACE-SERVICE.md](services/MARKETPLACE-SERVICE.md) | Маркетплейс |

## Диаграммы

### Архитектура системы

```
                    ┌─────────────┐
                    │   Client    │
                    └──────┬──────┘
                           │
                           ▼
                ┌─────────────────────┐
                │   API Gateway       │
                │      :8080         │
                └──────────┬──────────┘
                           │
      ┌────────┬────────┬──┴───┬────────┬────────┐
      ▼        ▼        ▼      ▼        ▼        ▼
  ┌───────┐┌───────┐┌───────┐┌───────┐┌───────┐
  │ User  ││Notif. ││Freela.││Conten.││Market.│
  │Service││Service││Service││Service││Service│
  │ :8000 ││ :8001 ││ :8002 ││ :8003 ││ :8004 │
  └───┬───┘└───┬───┘└───┬───┘└───┬───┘└───┬───┘
      └────────┴────────┴────────┴────────┘
                       │
           ┌───────────┴───────────┐
           ▼                       ▼
      ┌──────────┐            ┌──────────┐
      │PostgreSQL│            │  Redis   │
      │  :5432   │            │  :6379   │
      └──────────┘            └──────────┘
```

### База данных

```
PostgreSQL
├── user_service_db
│   ├── User
│   └── UserProfile
│
├── notification_service_db
│   ├── Notification
│   └── NotificationPreference
│
├── freelance_service_db
│   ├── Gig
│   ├── Order
│   ├── Review
│   └── Category
│
├── content_service_db
│   ├── Channel
│   ├── Post
│   └── Comment
│
└── marketplace_service_db
    ├── Product
    └── Category
```

## Быстрые ссылки

### Для разработчиков

- [Настройка окружения](DEVELOPMENT.md#настройка-окружения)
- [Структура проекта](DEVELOPMENT.md#структура-проекта)
- [Создание нового сервиса](DEVELOPMENT.md#разработка-нового-микросервиса)
- [Работа с БД](DEVELOPMENT.md#работа-с-базами-данных)
- [Тестирование](DEVELOPMENT.md#тестирование)
- [Стиль кода](DEVELOPMENT.md#стиль-кода)

### Для DevOps

- [Локальное развертывание](DEPLOYMENT.md#локальное-развертывание)
- [Production развертывание](DEPLOYMENT.md#production-развертывание)
- [Конфигурация Nginx](DEPLOYMENT.md#nginx-конфигурация)
- [SSL сертификаты](DEPLOYMENT.md#ssl-сертификаты-lets-encrypt)
- [Backup и восстановление](DEPLOYMENT.md#backup-и-восстановление)
- [Масштабирование](DEPLOYMENT.md#масштабирование)

### Для Frontend разработчиков

- [API Endpoints](API.md#api-endpoints)
- [Аутентификация](API.md#аутентификация)
- [Примеры запросов](API.md#примеры-запросов)
- [Коды ошибок](API.md#коды-ошибок)
- [Rate Limiting](API.md#rate-limiting)

## Статистика документации

- **Всего документов:** 12 файлов
- **Общий размер:** ~280 KB
- **API Endpoints:** 150+
- **Примеры кода:** 100+
- **Диаграммы:** 15+
- **Таблицы:** 50+

## Технологии

- **Backend:** Django 5.2.5, DRF 3.14.0, Python 3.11
- **Database:** PostgreSQL 16, Redis 7
- **Infrastructure:** Docker, Docker Compose, Gunicorn
- **Testing:** pytest, factory-boy
- **Security:** JWT, CORS, Rate Limiting

## Что документировано?

### Для каждого микросервиса:

- Обзор и назначение
- Структура проекта
- Модели данных (с таблицами полей)
- API Endpoints (с примерами)
- Конфигурация и переменные окружения
- Docker настройки
- Примеры использования
- Безопасность
- Производительность
- Troubleshooting

### Общая документация:

- Архитектура системы
- Паттерны и принципы
- Масштабируемость
- Мониторинг
- Развертывание (local, staging, production)
- Backup стратегии
- CI/CD
- Лучшие практики

## Примеры использования

### Регистрация пользователя

```bash
curl -X POST http://localhost:8080/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass123",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

### Создание услуги

```bash
curl -X POST http://localhost:8080/api/gigs/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Web Design Service",
    "description": "Professional web design",
    "category_id": 1
  }'
```

Больше примеров: [API.md](API.md)

## Вопросы и поддержка

### Частые вопросы

**Q: Как запустить проект локально?**
A: См. [Локальное развертывание](DEPLOYMENT.md#локальное-развертывание)

**Q: Как добавить новый микросервис?**
A: См. [Разработка нового микросервиса](DEVELOPMENT.md#разработка-нового-микросервиса)

**Q: Как работает аутентификация?**
A: См. [Аутентификация](API.md#аутентификация)

**Q: Как сделать backup?**
A: См. [Backup и восстановление](DEPLOYMENT.md#backup-и-восстановление)

### Получить помощь

- **Issues:** [GitHub Issues](https://github.com/loowpts/microservice-platform/issues)
- **Документация:** Вы здесь!
- **Email:** support@example.com

## Вклад в документацию

Нашли ошибку или хотите улучшить документацию?

1. Fork репозиторий
2. Создайте branch: `git checkout -b docs/improve-api-docs`
3. Внесите изменения
4. Commit: `git commit -m "docs: улучшить описание API endpoints"`
5. Push: `git push origin docs/improve-api-docs`
6. Создайте Pull Request

### Стиль документации

- Используйте Markdown
- Добавляйте примеры кода
- Используйте таблицы для структурированных данных
- Добавляйте диаграммы где возможно
- Ссылайтесь на другие документы
- Проверяйте орфографию

## Roadmap документации

- [ ] Добавить Postman коллекцию
- [ ] Создать видео туториалы
- [ ] Добавить OpenAPI/Swagger спецификацию
- [ ] Создать интерактивную документацию
- [ ] Добавить больше диаграмм
- [ ] Перевести на английский

## Версия документации

**Текущая версия:** 1.0.0
**Последнее обновление:** 2025-12-04
**Статус:** Актуально ✅

## Лицензия

Документация распространяется под [MIT License](../LICENSE)

---

**Приятного использования!** Если что-то непонятно - создавайте Issue или смотрите [INDEX.md](INDEX.md) для полной навигации.
