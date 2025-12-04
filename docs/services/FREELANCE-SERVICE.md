# Freelance Service

## Обзор

Freelance Service управляет всеми аспектами фрилансовой платформы: услуги (gigs), заказы, отзывы, портфолио, предложения и избранное. Сервис предоставляет полный функционал для фрилансеров и клиентов.

## Основная информация

- **Порт:** 8002
- **Framework:** Django 5.2.5 + DRF 3.14.0
- **Язык:** Python 3.11
- **Database:** PostgreSQL
- **Cache:** Redis
- **Apps:** gigs, orders, reviews, categories, portfolio, proposals, favorites, analytics, search

## Архитектура

```
┌─────────────────────────────────────────┐
│    Freelance Service :8002              │
├─────────────────────────────────────────┤
│  REST API Layer:                        │
│  - /api/gigs/                           │
│  - /api/orders/                         │
│  - /api/reviews/                        │
│  - /api/categories/                     │
│  - /api/portfolio/                      │
│  - /api/proposals/                      │
│  - /api/favorites/                      │
│  - /api/search/                         │
│                                         │
│  Models:                                │
│  - Gig, GigPackage, GigImage, GigTag   │
│  - Order, OrderDelivery, Dispute       │
│  - Review, ReviewReply                 │
│  - Category, Portfolio, Proposal       │
│  - Favorite                            │
└────────────────────────────────────────┘
         │
         ▼
    PostgreSQL (freelance_service_db)
```

## Структура проекта

```
freelance-service/
├── apps/
│   ├── gigs/
│   │   ├── models.py          # Gig, GigPackage, GigImage, GigTag
│   │   ├── views.py           # API views
│   │   ├── serializers.py      # DRF serializers
│   │   ├── urls.py
│   │   └── tests.py
│   ├── orders/
│   │   ├── models.py          # Order, OrderDelivery, Dispute
│   │   ├── views.py
│   │   ├── serializers.py
│   │   └── urls.py
│   ├── reviews/
│   │   ├── models.py          # Review, ReviewReply
│   │   ├── views.py
│   │   ├── serializers.py
│   │   └── urls.py
│   ├── categories/
│   │   ├── models.py          # Category
│   │   ├── views.py
│   │   └── urls.py
│   ├── portfolio/
│   │   ├── models.py          # Portfolio
│   │   ├── views.py
│   │   └── urls.py
│   ├── proposals/
│   │   ├── models.py          # Proposal
│   │   ├── views.py
│   │   └── urls.py
│   ├── favorites/
│   │   ├── models.py          # Favorite
│   │   ├── views.py
│   │   └── urls.py
│   ├── analytics/
│   │   ├── views.py           # Аналитика продаж
│   │   └── urls.py
│   ├── search/
│   │   ├── views.py           # Полнотекстовый поиск
│   │   └── urls.py
│   └── __init__.py
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Модели данных

### Gig (Услуга)

| Поле | Тип | Описание |
|------|-----|---------|
| id | Integer | Первичный ключ |
| seller_id | Integer | ID продавца |
| category | ForeignKey | Категория услуги |
| title | CharField | Название услуги (макс. 200 символов) |
| slug | SlugField | URL-friendly ID (unique) |
| description | TextField | Подробное описание (макс. 5000 символов) |
| main_image | URLField | Основное изображение |
| status | CharField | Статус (draft, pending_approval, active, paused, archived) |
| views_count | PositiveInteger | Количество просмотров |
| orders_count | PositiveInteger | Количество завершенных заказов |
| rating_average | Decimal | Средняя оценка (0.00-5.00) |
| reviews_count | PositiveInteger | Количество отзывов |
| created_at | DateTime | Дата создания |
| updated_at | DateTime | Дата обновления |

**Методы:**
- `update_rating()` - обновить рейтинг из отзывов
- `update_orders_count()` - обновить количество заказов
- `increment_views()` - увеличить счетчик просмотров

### GigPackage (Пакет услуги)

| Поле | Тип | Описание |
|------|-----|---------|
| id | Integer | Первичный ключ |
| gig | ForeignKey | Связь с Gig |
| package_type | CharField | Тип пакета (basic, standard, premium) |
| name | CharField | Название пакета (макс. 100 символов) |
| description | TextField | Описание пакета (макс. 1000 символов) |
| price | Decimal | Цена пакета |
| delivery_time | PositiveInteger | Время доставки в днях |
| revisions | PositiveInteger | Количество доступных правок |
| features | JSONField | Список особенностей |

### Order (Заказ)

| Поле | Тип | Описание |
|------|-----|---------|
| id | Integer | Первичный ключ |
| gig | ForeignKey | Связь с Gig |
| package | ForeignKey | Связь с GigPackage |
| buyer_id | Integer | ID покупателя |
| seller_id | Integer | ID продавца |
| status | CharField | Статус (pending, in_progress, delivered, completed, cancelled, disputed) |
| price | Decimal | Цена заказа |
| delivery_time | PositiveInteger | Время доставки в днях |
| requirements | TextField | Требования покупателя |
| deadline | DateTime | Срок выполнения |
| delivered_at | DateTime | Дата доставки результата |
| completed_at | DateTime | Дата завершения |
| created_at | DateTime | Дата создания |
| updated_at | DateTime | Дата обновления |

### OrderDelivery (Доставка результата)

| Поле | Тип | Описание |
|------|-----|---------|
| id | Integer | Первичный ключ |
| order | ForeignKey | Связь с Order |
| message | TextField | Сообщение с результатом (макс. 2000 символов) |
| file_url | URLField | URL файла результата |
| created_at | DateTime | Дата доставки |

### Review (Отзыв)

| Поле | Тип | Описание |
|------|-----|---------|
| id | Integer | Первичный ключ |
| order | OneToOneField | Связь с Order |
| gig | ForeignKey | Связь с Gig |
| buyer_id | Integer | ID оставившего отзыв |
| seller_id | Integer | ID продавца (для индексации) |
| rating | PositiveSmallInteger | Общая оценка (1-5) |
| comment | TextField | Текст отзыва (макс. 2000 символов) |
| communication_rating | PositiveSmallInteger | Оценка общения (1-5) |
| service_quality_rating | PositiveSmallInteger | Оценка качества (1-5) |
| delivery_rating | PositiveSmallInteger | Оценка доставки (1-5) |
| is_active | Boolean | Активен ли отзыв |
| created_at | DateTime | Дата создания |
| updated_at | DateTime | Дата обновления |

### Dispute (Спор)

| Поле | Тип | Описание |
|------|-----|---------|
| id | Integer | Первичный ключ |
| order | OneToOneField | Связь с Order |
| created_by_id | Integer | ID создавшего спор |
| reason | TextField | Причина спора (макс. 2000 символов) |
| status | CharField | Статус (open, in_review, resolved, closed) |
| resolved_by_id | Integer | ID модератора, который разрешил спор |
| resolution | TextField | Описание разрешения |
| winner_side | CharField | Сторона-победитель (buyer/seller/none) |
| resolved_at | DateTime | Дата разрешения |
| created_at | DateTime | Дата создания |
| updated_at | DateTime | Дата обновления |

## API Endpoints

### Услуги (Gigs)

#### Получить все услуги

```http
GET /api/gigs/?page=1&category=web-design&status=active&search=logo&ordering=-rating_average
Authorization: Bearer {access_token}
```

**Query Parameters:**
- `page` (int) - номер страницы
- `category` (string) - фильтр по категории
- `status` (string) - фильтр по статусу
- `search` (string) - поиск по названию/описанию
- `min_price`, `max_price` - диапазон цен
- `min_rating` - минимальный рейтинг
- `ordering` - сортировка (rating_average, created_at, price)

**Response (200 OK):**
```json
{
  "count": 150,
  "next": "http://localhost:8002/api/gigs/?page=2",
  "results": [
    {
      "id": 1,
      "seller_id": 5,
      "title": "Professional Logo Design",
      "slug": "professional-logo-design",
      "description": "I will create...",
      "category": {
        "id": 1,
        "name": "Logo Design",
        "slug": "logo-design"
      },
      "main_image": "https://...",
      "status": "active",
      "views_count": 250,
      "orders_count": 45,
      "rating_average": 4.8,
      "reviews_count": 32,
      "packages": [
        {
          "id": 1,
          "package_type": "basic",
          "name": "Basic Logo",
          "price": "50.00",
          "delivery_time": 3,
          "features": ["Logo design", "1 revision"]
        }
      ]
    }
  ]
}
```

#### Создать услугу

```http
POST /api/gigs/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "title": "Web Design Service",
  "category_id": 1,
  "description": "I will design...",
  "packages": [
    {
      "package_type": "basic",
      "name": "Basic Package",
      "price": "100.00",
      "delivery_time": 5,
      "revisions": 1,
      "features": ["Feature 1", "Feature 2"]
    }
  ]
}
```

**Response (201 Created):**
```json
{
  "id": 2,
  "seller_id": 5,
  "title": "Web Design Service",
  "slug": "web-design-service",
  "status": "draft",
  "packages": [...]
}
```

#### Получить услугу по ID

```http
GET /api/gigs/{id}/
```

**Response (200 OK):**
```json
{
  "id": 1,
  "seller_id": 5,
  "title": "Professional Logo Design",
  "description": "...",
  "category": {...},
  "packages": [...],
  "images": [...],
  "tags": [...]
}
```

#### Обновить услугу

```http
PATCH /api/gigs/{id}/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "title": "Updated Logo Design",
  "description": "Updated description"
}
```

#### Опубликовать услугу

```http
POST /api/gigs/{id}/publish/
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "status": "pending_approval",
  "message": "Gig submitted for approval"
}
```

#### Добавить изображение к услуге

```http
POST /api/gigs/{id}/images/
Authorization: Bearer {access_token}
Content-Type: multipart/form-data

{
  "image": <binary_file>,
  "is_primary": false,
  "order": 1,
  "caption": "Example image"
}
```

### Заказы (Orders)

#### Создать заказ

```http
POST /api/orders/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "gig_id": 1,
  "package_id": 1,
  "requirements": "Please include..."
}
```

**Response (201 Created):**
```json
{
  "id": 101,
  "gig": {...},
  "package": {...},
  "buyer_id": 5,
  "seller_id": 3,
  "status": "pending",
  "price": "100.00",
  "deadline": "2025-12-09T10:00:00Z",
  "created_at": "2025-12-04T10:00:00Z"
}
```

#### Получить заказы пользователя

```http
GET /api/orders/?status=in_progress&role=seller
Authorization: Bearer {access_token}
```

**Query Parameters:**
- `status` (string) - фильтр по статусу
- `role` (string) - as_buyer или as_seller

**Response (200 OK):**
```json
{
  "count": 15,
  "results": [...]
}
```

#### Подтвердить заказ (продавец)

```http
POST /api/orders/{id}/accept/
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "id": 101,
  "status": "in_progress",
  "message": "Order accepted"
}
```

#### Доставить результат

```http
POST /api/orders/{id}/deliver/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "message": "Here is your design...",
  "file_url": "https://..."
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "order_id": 101,
  "message": "Here is your design...",
  "file_url": "https://...",
  "created_at": "2025-12-04T10:00:00Z"
}
```

#### Завершить заказ (покупатель)

```http
POST /api/orders/{id}/complete/
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "id": 101,
  "status": "completed",
  "completed_at": "2025-12-04T10:00:00Z"
}
```

#### Отменить заказ

```http
POST /api/orders/{id}/cancel/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "reason": "Changed my mind"
}
```

### Отзывы (Reviews)

#### Создать отзыв

```http
POST /api/reviews/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "order_id": 101,
  "rating": 5,
  "comment": "Great service!",
  "communication_rating": 5,
  "service_quality_rating": 5,
  "delivery_rating": 4
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "order_id": 101,
  "gig_id": 1,
  "rating": 5,
  "comment": "Great service!",
  "created_at": "2025-12-04T10:00:00Z"
}
```

#### Получить отзывы услуги

```http
GET /api/gigs/{gig_id}/reviews/?page=1&ordering=-rating
```

**Response (200 OK):**
```json
{
  "count": 32,
  "results": [
    {
      "id": 1,
      "rating": 5,
      "comment": "Great service!",
      "buyer_name": "John",
      "created_at": "2025-12-04T10:00:00Z"
    }
  ]
}
```

#### Ответить на отзыв

```http
POST /api/reviews/{id}/reply/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "message": "Thank you for the feedback!"
}
```

### Категории (Categories)

#### Получить все категории

```http
GET /api/categories/
```

**Response (200 OK):**
```json
{
  "count": 25,
  "results": [
    {
      "id": 1,
      "name": "Logo Design",
      "slug": "logo-design",
      "description": "Logo design services...",
      "gigs_count": 150
    }
  ]
}
```

### Портфолио (Portfolio)

#### Добавить проект в портфолио

```http
POST /api/portfolio/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "title": "Branding Project",
  "description": "Full branding...",
  "image_url": "https://...",
  "url": "https://example.com",
  "price": "5000.00"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "seller_id": 5,
  "title": "Branding Project",
  "created_at": "2025-12-04T10:00:00Z"
}
```

### Предложения (Proposals)

#### Получить все предложения

```http
GET /api/proposals/?status=pending
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "count": 3,
  "results": [...]
}
```

### Избранное (Favorites)

#### Добавить услугу в избранное

```http
POST /api/favorites/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "gig_id": 1
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "user_id": 5,
  "gig_id": 1
}
```

#### Получить избранные услуги

```http
GET /api/favorites/?page=1
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "count": 12,
  "results": [...]
}
```

#### Удалить из избранного

```http
DELETE /api/favorites/{gig_id}/
Authorization: Bearer {access_token}
```

### Поиск (Search)

#### Полнотекстовый поиск

```http
GET /api/search/?q=logo+design&filters=category:1,min_price:50,max_price:500
```

**Response (200 OK):**
```json
{
  "count": 45,
  "results": [...]
}
```

### Аналитика (Analytics)

#### Получить аналитику продавца

```http
GET /api/analytics/seller-stats/
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "total_gigs": 5,
  "active_gigs": 4,
  "total_orders": 120,
  "completed_orders": 115,
  "average_rating": 4.8,
  "total_earnings": "8500.00",
  "this_month_earnings": "1200.00"
}
```

## Конфигурация

### Переменные окружения

```bash
# Django
DEBUG=False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1,freelance-service

# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=freelance_service_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/4

# Services
USER_SERVICE_URL=http://user-service:8000
NOTIFICATION_SERVICE_URL=http://notification-service:8001

# Search (Elasticsearch)
ELASTICSEARCH_URL=http://elasticsearch:9200

# File Storage (AWS S3)
USE_S3=False
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_STORAGE_BUCKET_NAME=your-bucket
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

EXPOSE 8002

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8002/api/health/ || exit 1

ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8002", "--workers", "3"]
```

## Примеры использования

### Python пример - Создание услуги

```python
import requests

BASE_URL = 'http://localhost:8002'
access_token = 'your_token'

# Создать услугу
gig_data = {
    'title': 'Professional Web Design',
    'category_id': 1,
    'description': 'I will design...',
    'packages': [
        {
            'package_type': 'basic',
            'name': 'Basic Package',
            'price': '100.00',
            'delivery_time': 5,
            'revisions': 1,
            'features': ['Design', 'Revisions']
        }
    ]
}

headers = {'Authorization': f'Bearer {access_token}'}
response = requests.post(
    f'{BASE_URL}/api/gigs/',
    json=gig_data,
    headers=headers
)
print(response.json())
```

### JavaScript пример - Получение услуг

```javascript
const BASE_URL = 'http://localhost:8002';

async function getGigs(category, minPrice, maxPrice) {
  const params = new URLSearchParams({
    category: category,
    min_price: minPrice,
    max_price: maxPrice,
    ordering: '-rating_average'
  });

  const response = await fetch(
    `${BASE_URL}/api/gigs/?${params}`
  );
  return await response.json();
}

// Использование
getGigs('web-design', 50, 500).then(gigs => {
  console.log(`Found ${gigs.count} gigs`);
});
```

## Troubleshooting

```bash
# Проверить логи
docker-compose logs freelance-service

# Миграции БД
docker-compose exec freelance-service python manage.py migrate

# Создать тестовые данные
docker-compose exec freelance-service python manage.py loaddata fixtures/categories.json
```

## Roadmap

- [ ] Video portfolios
- [ ] Advanced analytics dashboard
- [ ] AI-powered recommendations
- [ ] Multi-language support
- [ ] Subscription-based services
- [ ] Team collaboration features

## См. также

- [User Service](USER-SERVICE.md)
- [Notification Service](NOTIFICATION-SERVICE.md)
- [API Gateway Service](API-GATEWAY.md)
- [Архитектура системы](../ARCHITECTURE.md)
