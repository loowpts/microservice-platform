# Marketplace Service

## Обзор

Marketplace Service управляет электронной коммерцией платформы: товары, категории, поиск, заказы, отзывы и избранное. Сервис предоставляет полный функционал для продавцов и покупателей товаров.

## Основная информация

- **Порт:** 8004
- **Framework:** Django 5.2.5 + DRF 3.14.0
- **Язык:** Python 3.11
- **Database:** PostgreSQL
- **Cache:** Redis
- **Apps:** products, categories, orders, reviews, favorites, search

## Архитектура

```
┌──────────────────────────────────────┐
│    Marketplace Service :8004         │
├──────────────────────────────────────┤
│  REST API Layer:                     │
│  - /api/products/                    │
│  - /api/categories/                  │
│  - /api/orders/                      │
│  - /api/reviews/                     │
│  - /api/favorites/                   │
│  - /api/search/                      │
│                                      │
│  Models:                             │
│  - Product, ProductImage            │
│  - Category                          │
│  - Order, OrderItem                  │
│  - Review                            │
│  - Favorite                          │
└──────────────────────────────────────┘
         │
         ▼
    PostgreSQL (marketplace_service_db)
```

## Структура проекта

```
marketplace-service/
├── apps/
│   ├── products/
│   │   ├── models.py          # Product, ProductImage
│   │   ├── views.py           # API views
│   │   ├── serializers.py      # DRF serializers
│   │   ├── urls.py
│   │   ├── admin.py
│   │   └── tests.py
│   ├── categories/
│   │   ├── models.py          # Category
│   │   ├── views.py
│   │   └── urls.py
│   ├── orders/
│   │   ├── models.py          # Order, OrderItem
│   │   ├── views.py
│   │   ├── serializers.py
│   │   └── urls.py
│   ├── reviews/
│   │   ├── models.py          # Review
│   │   ├── views.py
│   │   └── urls.py
│   ├── favorites/
│   │   ├── models.py          # Favorite
│   │   ├── views.py
│   │   └── urls.py
│   ├── search/
│   │   ├── views.py           # Полнотекстовый поиск
│   │   └── urls.py
│   ├── common/
│   │   └── proxies.py         # Proxies для моделей
│   └── __init__.py
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── tests/
│   ├── test_products/
│   ├── test_categories/
│   ├── test_reviews/
│   ├── test_favorites/
│   └── test_search/
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Модели данных

### Category (Категория)

| Поле | Тип | Описание |
|------|-----|---------|
| id | Integer | Первичный ключ |
| name | CharField | Название категории (unique, макс. 150 символов) |
| slug | SlugField | URL-friendly ID (unique) |
| description | TextField | Описание категории |
| parent | ForeignKey | Для подкатегорий (self-relation, nullable) |
| image_url | URLField | Изображение категории |
| position | PositiveInteger | Позиция для сортировки |
| products_count | PositiveInteger | Кэшированное количество товаров |

### Product (Товар)

| Поле | Тип | Описание |
|------|-----|---------|
| id | Integer | Первичный ключ |
| category | ForeignKey | Связь с Category |
| title | CharField | Название товара (unique, макс. 150 символов) |
| slug | SlugField | URL-friendly ID (unique) |
| description | TextField | Подробное описание (макс. 1000 символов) |
| price | Decimal | Цена товара |
| old_price | Decimal | Старая цена (для скидок, nullable) |
| main_image | URLField | Основное изображение товара |
| seller_id | Integer | ID продавца |
| condition | CharField | Состояние (new, used, refurbished) |
| status | CharField | Статус (active, sold, archived, draft) |
| city | CharField | Город (макс. 100 символов) |
| quantity | PositiveInteger | Доступное количество |
| views_count | PositiveInteger | Количество просмотров |
| rating_average | Decimal | Средняя оценка (0.00-5.00, nullable) |
| reviews_count | PositiveInteger | Количество отзывов |
| created_at | DateTime | Дата создания |
| updated_at | DateTime | Дата обновления |

**Методы:**
- `get_discount_percent()` - вычислить процент скидки
- `update_rating()` - обновить рейтинг из отзывов
- `increment_views()` - увеличить счетчик просмотров
- `is_available()` - проверить доступен ли товар

**Индексы:**
- (seller_id, status)
- (category, status)
- (created_at)

### ProductImage (Изображение товара)

| Поле | Тип | Описание |
|------|-----|---------|
| id | Integer | Первичный ключ |
| product | ForeignKey | Связь с Product |
| image_url | URLField | URL изображения (макс. 500 символов) |
| is_primary | Boolean | Является ли основным изображением |
| order | PositiveInteger | Порядок вывода |

### Review (Отзыв)

| Поле | Тип | Описание |
|------|-----|---------|
| id | Integer | Первичный ключ |
| product | ForeignKey | Связь с Product |
| buyer_id | Integer | ID покупателя |
| rating | PositiveSmallInteger | Оценка (1-5) |
| comment | TextField | Текст отзыва (макс. 1000 символов) |
| verified_purchase | Boolean | Подтвержденная покупка |
| helpful_count | PositiveInteger | Количество "полезный" |
| created_at | DateTime | Дата создания |
| updated_at | DateTime | Дата обновления |

### Favorite (Избранное)

| Поле | Тип | Описание |
|------|-----|---------|
| id | Integer | Первичный ключ |
| user_id | Integer | ID пользователя |
| product | ForeignKey | Связь с Product |
| created_at | DateTime | Дата добавления |

**Unique Together:** (user_id, product_id)

## API Endpoints

### Товары (Products)

#### Получить все товары

```http
GET /api/products/?page=1&category=electronics&condition=new&city=Moscow&min_price=100&max_price=5000&search=laptop&ordering=-created_at
```

**Query Parameters:**
- `page` (int) - номер страницы (default: 1)
- `category` (string) - фильтр по категории (slug)
- `condition` (string) - фильтр по состоянию (new, used, refurbished)
- `city` (string) - фильтр по городу
- `min_price`, `max_price` - диапазон цен
- `search` (string) - полнотекстовый поиск
- `ordering` - сортировка (-created_at, price, -rating_average)
- `status` (string) - фильтр по статусу (active, sold)

**Response (200 OK):**
```json
{
  "count": 523,
  "next": "http://localhost:8004/api/products/?page=2",
  "results": [
    {
      "id": 1,
      "title": "MacBook Pro 16\"",
      "slug": "macbook-pro-16",
      "description": "2024 MacBook Pro...",
      "category": {
        "id": 5,
        "name": "Computers",
        "slug": "computers"
      },
      "price": "2500.00",
      "old_price": "3000.00",
      "discount_percent": 17,
      "main_image": "https://...",
      "seller_id": 10,
      "condition": "new",
      "status": "active",
      "city": "Moscow",
      "quantity": 3,
      "views_count": 450,
      "rating_average": 4.8,
      "reviews_count": 15,
      "created_at": "2025-12-01T10:00:00Z"
    }
  ]
}
```

#### Создать товар (продавец)

```http
POST /api/products/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "category_id": 5,
  "title": "iPhone 15 Pro",
  "description": "Newest iPhone with advanced features...",
  "price": "999.00",
  "old_price": "1099.00",
  "condition": "new",
  "city": "Moscow",
  "quantity": 5,
  "main_image": "https://..."
}
```

**Response (201 Created):**
```json
{
  "id": 2,
  "title": "iPhone 15 Pro",
  "slug": "iphone-15-pro",
  "price": "999.00",
  "status": "draft",
  "created_at": "2025-12-04T10:00:00Z"
}
```

#### Получить товар

```http
GET /api/products/{id}/
```

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "MacBook Pro 16\"",
  "slug": "macbook-pro-16",
  "description": "2024 MacBook Pro with M3 Pro...",
  "category": {...},
  "price": "2500.00",
  "old_price": "3000.00",
  "discount_percent": 17,
  "seller": {
    "id": 10,
    "first_name": "John",
    "email": "seller@example.com"
  },
  "condition": "new",
  "status": "active",
  "city": "Moscow",
  "quantity": 3,
  "views_count": 451,
  "rating_average": 4.8,
  "reviews_count": 15,
  "images": [
    {
      "id": 1,
      "image_url": "https://...",
      "is_primary": true
    }
  ],
  "created_at": "2025-12-01T10:00:00Z"
}
```

#### Обновить товар (продавец)

```http
PATCH /api/products/{id}/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "title": "Updated title",
  "price": "2400.00",
  "quantity": 2
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "Updated title",
  "price": "2400.00",
  "quantity": 2,
  "updated_at": "2025-12-04T10:00:00Z"
}
```

#### Опубликовать товар (продавец)

```http
POST /api/products/{id}/publish/
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "status": "active",
  "message": "Product published successfully"
}
```

#### Удалить товар (продавец)

```http
DELETE /api/products/{id}/
Authorization: Bearer {access_token}
```

**Response (204 No Content)**

#### Добавить изображение к товару

```http
POST /api/products/{id}/images/
Authorization: Bearer {access_token}
Content-Type: multipart/form-data

{
  "image": <binary_file>,
  "is_primary": false,
  "order": 2
}
```

**Response (201 Created):**
```json
{
  "id": 2,
  "product_id": 1,
  "image_url": "https://...",
  "is_primary": false,
  "order": 2
}
```

### Категории (Categories)

#### Получить все категории

```http
GET /api/categories/?parent_id=null
```

**Query Parameters:**
- `parent_id` - фильтр по родительской категории

**Response (200 OK):**
```json
{
  "count": 12,
  "results": [
    {
      "id": 1,
      "name": "Electronics",
      "slug": "electronics",
      "description": "Electronic devices...",
      "image_url": "https://...",
      "products_count": 250,
      "subcategories": [
        {
          "id": 5,
          "name": "Computers",
          "slug": "computers",
          "products_count": 80
        }
      ]
    }
  ]
}
```

#### Получить категорию с товарами

```http
GET /api/categories/{id}/products/?page=1
```

**Response (200 OK):**
```json
{
  "category": {
    "id": 1,
    "name": "Electronics",
    "slug": "electronics",
    "products_count": 250
  },
  "products": {
    "count": 250,
    "results": [...]
  }
}
```

### Заказы (Orders)

#### Создать заказ

```http
POST /api/orders/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "items": [
    {
      "product_id": 1,
      "quantity": 1
    },
    {
      "product_id": 2,
      "quantity": 2
    }
  ],
  "delivery_address": "123 Main St, Moscow, Russia",
  "phone": "+7-999-123-4567"
}
```

**Response (201 Created):**
```json
{
  "id": 101,
  "buyer_id": 5,
  "items": [
    {
      "product_id": 1,
      "quantity": 1,
      "price": "2500.00"
    }
  ],
  "total_price": "3500.00",
  "status": "pending",
  "created_at": "2025-12-04T10:00:00Z"
}
```

#### Получить заказы пользователя

```http
GET /api/orders/?page=1&status=completed&role=buyer
Authorization: Bearer {access_token}
```

**Query Parameters:**
- `status` - фильтр по статусу
- `role` - as_buyer или as_seller

**Response (200 OK):**
```json
{
  "count": 15,
  "results": [...]
}
```

#### Получить заказ

```http
GET /api/orders/{id}/
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "id": 101,
  "buyer_id": 5,
  "items": [...],
  "total_price": "3500.00",
  "status": "completed",
  "delivery_address": "123 Main St, Moscow",
  "tracking_number": "TRK123456789",
  "created_at": "2025-12-04T10:00:00Z"
}
```

#### Подтвердить заказ (продавец)

```http
POST /api/orders/{id}/confirm/
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "id": 101,
  "status": "confirmed",
  "message": "Order confirmed"
}
```

### Отзывы (Reviews)

#### Создать отзыв

```http
POST /api/reviews/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "product_id": 1,
  "rating": 5,
  "comment": "Excellent product! Highly recommended.",
  "verified_purchase": true
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "product_id": 1,
  "buyer_id": 5,
  "rating": 5,
  "comment": "Excellent product! Highly recommended.",
  "verified_purchase": true,
  "created_at": "2025-12-04T10:00:00Z"
}
```

#### Получить отзывы товара

```http
GET /api/products/{product_id}/reviews/?page=1&ordering=-rating
```

**Response (200 OK):**
```json
{
  "count": 15,
  "average_rating": 4.7,
  "rating_distribution": {
    "5": 10,
    "4": 3,
    "3": 1,
    "2": 0,
    "1": 0
  },
  "results": [...]
}
```

#### Отметить отзыв как полезный

```http
POST /api/reviews/{id}/helpful/
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "helpful_count": 5
}
```

### Избранное (Favorites)

#### Добавить товар в избранное

```http
POST /api/favorites/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "product_id": 1
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "user_id": 5,
  "product_id": 1,
  "created_at": "2025-12-04T10:00:00Z"
}
```

#### Получить избранные товары

```http
GET /api/favorites/?page=1
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "count": 12,
  "results": [
    {
      "id": 1,
      "product": {
        "id": 1,
        "title": "MacBook Pro 16\"",
        "price": "2500.00"
      },
      "created_at": "2025-12-04T10:00:00Z"
    }
  ]
}
```

#### Удалить из избранного

```http
DELETE /api/favorites/{product_id}/
Authorization: Bearer {access_token}
```

**Response (204 No Content)**

### Поиск (Search)

#### Полнотекстовый поиск

```http
GET /api/search/?q=laptop&category=electronics&min_price=1000&max_price=3000&filters=condition:new,city:Moscow
```

**Query Parameters:**
- `q` - поисковый запрос
- `category` - фильтр по категории
- `min_price`, `max_price` - диапазон цен
- `filters` - дополнительные фильтры

**Response (200 OK):**
```json
{
  "count": 45,
  "query": "laptop",
  "time": 0.15,
  "results": [...]
}
```

## Конфигурация

### Переменные окружения

```bash
# Django
DEBUG=False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1,marketplace-service

# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=marketplace_service_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/6

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

# Payment
STRIPE_API_KEY=your-stripe-key
STRIPE_WEBHOOK_SECRET=your-webhook-secret

# Security
SECURE_SSL_REDIRECT=False
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://yourapp.com
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

EXPOSE 8004

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8004/api/health/ || exit 1

ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8004", "--workers", "3"]
```

## Примеры использования

### Python пример

```python
import requests

BASE_URL = 'http://localhost:8004'
access_token = 'your_token'
headers = {'Authorization': f'Bearer {access_token}'}

# Получить товары с фильтрацией
response = requests.get(
    f'{BASE_URL}/api/products/',
    params={
        'category': 'electronics',
        'min_price': 100,
        'max_price': 5000,
        'condition': 'new',
        'city': 'Moscow'
    }
)
products = response.json()
print(f"Found {products['count']} products")

# Создать товар
product_data = {
    'category_id': 5,
    'title': 'Gaming Laptop',
    'description': 'High-performance gaming laptop...',
    'price': '1500.00',
    'condition': 'new',
    'city': 'Moscow',
    'quantity': 3
}
response = requests.post(
    f'{BASE_URL}/api/products/',
    json=product_data,
    headers=headers
)
product = response.json()
print(f"Product created: {product['id']}")

# Создать заказ
order_data = {
    'items': [
        {'product_id': 1, 'quantity': 1},
        {'product_id': 2, 'quantity': 2}
    ],
    'delivery_address': '123 Main St, Moscow',
    'phone': '+7-999-123-4567'
}
response = requests.post(
    f'{BASE_URL}/api/orders/',
    json=order_data,
    headers=headers
)
order = response.json()
print(f"Order created: {order['id']}")

# Добавить товар в избранное
favorite_data = {'product_id': 1}
response = requests.post(
    f'{BASE_URL}/api/favorites/',
    json=favorite_data,
    headers=headers
)
print("Product added to favorites!")

# Оставить отзыв
review_data = {
    'product_id': 1,
    'rating': 5,
    'comment': 'Excellent product!',
    'verified_purchase': True
}
response = requests.post(
    f'{BASE_URL}/api/reviews/',
    json=review_data,
    headers=headers
)
print("Review posted!")
```

### JavaScript пример

```javascript
const BASE_URL = 'http://localhost:8004';
const ACCESS_TOKEN = localStorage.getItem('access_token');

// Получить популярные товары
async function getPopularProducts() {
  const response = await fetch(
    `${BASE_URL}/api/products/?ordering=-views_count&limit=10`
  );
  return await response.json();
}

// Поиск товаров
async function searchProducts(query, filters = {}) {
  const params = new URLSearchParams({
    q: query,
    ...filters
  });

  const response = await fetch(
    `${BASE_URL}/api/search/?${params}`
  );
  return await response.json();
}

// Создать заказ
async function createOrder(items, address) {
  const response = await fetch(`${BASE_URL}/api/orders/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${ACCESS_TOKEN}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      items,
      delivery_address: address
    })
  });
  return await response.json();
}

// Использование
searchProducts('laptop', {
  category: 'electronics',
  min_price: 1000,
  max_price: 3000
}).then(results => {
  console.log(`Found ${results.count} products`);
  results.results.forEach(product => {
    console.log(`${product.title}: ${product.price}`);
  });
});
```

## Тестирование

```bash
# Запуск тестов
python manage.py test apps.products

# Тесты с покрытием
coverage run --source='apps' manage.py test
coverage report
coverage html

# Отдельные тесты
pytest tests/test_products/test_models.py -v
pytest tests/test_search/ -v
```

## Безопасность

1. **Валидация товаров** - проверка цен, описаний
2. **Контроль доступа** - только продавцы могут редактировать свои товары
3. **Предотвращение мошенничества** - отслеживание подозрительной активности
4. **Защита платежей** - интеграция с Stripe для безопасных платежей

## Производительность

1. **Кэширование** - товары и категории кэшируются
2. **Оптимизация БД** - индексы на часто используемые поля
3. **Полнотекстовый поиск** - использование Elasticsearch
4. **Асинхронные операции** - обновление рейтингов в фоне
5. **CDN** - доставка изображений через CDN

## Troubleshooting

```bash
# Проверить логи
docker-compose logs marketplace-service

# Миграции БД
docker-compose exec marketplace-service python manage.py migrate

# Загрузить тестовые категории
docker-compose exec marketplace-service python manage.py loaddata fixtures/categories.json

# Очистить Redis кэш
redis-cli -n 6 FLUSHDB
```

## Roadmap

- [ ] Advanced filtering и faceted search
- [ ] Wishlist functionality
- [ ] Product recommendations
- [ ] Seller analytics dashboard
- [ ] Multi-currency support
- [ ] Auction functionality
- [ ] Subscription products

## См. также

- [User Service](USER-SERVICE.md)
- [Freelance Service](FREELANCE-SERVICE.md)
- [Notification Service](NOTIFICATION-SERVICE.md)
- [API Gateway Service](API-GATEWAY.md)
- [Архитектура системы](../ARCHITECTURE.md)
