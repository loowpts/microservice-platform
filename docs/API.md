# API Documentation

Полная документация API для всех микросервисов платформы.

## Содержание

- [Базовая информация](#базовая-информация)
- [Аутентификация](#аутентификация)
- [User Service API](#user-service-api)
- [Notification Service API](#notification-service-api)
- [Freelance Service API](#freelance-service-api)
- [Content Service API](#content-service-api)
- [Marketplace Service API](#marketplace-service-api)
- [Коды ошибок](#коды-ошибок)
- [Rate Limiting](#rate-limiting)

## Базовая информация

### Base URLs

Все запросы проходят через API Gateway:

```
Production:  https://yourdomain.com/api
Development: http://localhost:8080/api
```

### Content Type

```
Content-Type: application/json
```

### Формат ответов

Все ответы возвращаются в формате JSON:

```json
{
  "data": {},
  "message": "Success",
  "status": 200
}
```

Ошибки:

```json
{
  "error": "Error description",
  "details": {},
  "status": 400
}
```

## Аутентификация

### JWT Tokens

Платформа использует JWT токены для аутентификации.

#### Получение токенов

**Endpoint:** `POST /api/auth/login/`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_freelancer": false,
    "is_seller": false
  }
}
```

#### Использование токена

Добавьте токен в header:

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

#### Обновление токена

**Endpoint:** `POST /api/auth/refresh/`

**Request:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### Проверка токена

**Endpoint:** `POST /api/auth/verify/`

**Request:**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:**
```json
{
  "valid": true,
  "user_id": 1
}
```

## User Service API

### Регистрация

**Endpoint:** `POST /api/users/`

**Доступ:** Публичный

**Request:**
```json
{
  "email": "newuser@example.com",
  "password": "securePassword123",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "email": "newuser@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "date_joined": "2025-12-04T10:00:00Z"
}
```

### Вход

**Endpoint:** `POST /api/auth/login/`

См. [Аутентификация](#аутентификация)

### Выход

**Endpoint:** `POST /api/auth/logout/`

**Auth:** Required

**Request:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:** `200 OK`
```json
{
  "message": "Successfully logged out"
}
```

### Получить текущего пользователя

**Endpoint:** `GET /api/auth/me/`

**Auth:** Required

**Response:** `200 OK`
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_freelancer": true,
  "is_seller": false,
  "is_verified": true,
  "profile": {
    "avatar": "https://example.com/media/avatars/user1.jpg",
    "bio": "Full-stack developer",
    "is_public": true
  }
}
```

### Получить профиль

**Endpoint:** `GET /api/profile/`

**Auth:** Required (владелец или staff)

**Response:** `200 OK`
```json
{
  "id": 1,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "avatar": "https://example.com/media/avatars/user1.jpg",
  "bio": "Full-stack developer with 5 years experience",
  "is_public": true,
  "timezone": "UTC",
  "created_at": "2025-01-01T10:00:00Z"
}
```

### Обновить профиль

**Endpoint:** `PUT /api/profile/update/`

**Auth:** Required

**Request:**
```json
{
  "first_name": "John",
  "last_name": "Smith",
  "bio": "Updated bio",
  "avatar": "base64_encoded_image_or_url",
  "is_public": true
}
```

**Response:** `200 OK`

### Установить роль

**Endpoint:** `POST /api/set-role/`

**Auth:** Required (только staff)

**Request:**
```json
{
  "user_id": 5,
  "is_freelancer": true,
  "is_seller": false,
  "is_moderator": false
}
```

**Response:** `200 OK`

## Notification Service API

### Отправить уведомление

**Endpoint:** `POST /api/notifications/send/`

**Auth:** Required (обычно используется сервисами)

**Request:**
```json
{
  "user_id": 1,
  "type": "email",
  "event": "order_created",
  "title": "New Order",
  "message": "You have a new order!",
  "email_to": "user@example.com",
  "email_subject": "New Order #123",
  "data": {
    "order_id": 123,
    "amount": "50.00"
  }
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "status": "pending",
  "message": "Notification created"
}
```

### Получить уведомления пользователя

**Endpoint:** `GET /api/notifications/user/{user_id}/`

**Auth:** Required

**Query Parameters:**
- `status` - pending, sent, failed, read
- `type` - email, in_app, push
- `unread_only` - true/false
- `limit` - количество (default: 50)

**Response:** `200 OK`
```json
{
  "notifications": [
    {
      "id": 1,
      "type": "in_app",
      "event": "order_created",
      "title": "New Order",
      "message": "You have a new order!",
      "status": "sent",
      "read_at": null,
      "created_at": "2025-12-04T10:00:00Z",
      "data": {
        "order_id": 123
      }
    }
  ],
  "unread_count": 5,
  "total": 25
}
```

### Отметить как прочитанное

**Endpoint:** `POST /api/notifications/{notification_id}/read/`

**Auth:** Required

**Response:** `200 OK`
```json
{
  "message": "Notification marked as read"
}
```

### Отметить все как прочитанные

**Endpoint:** `POST /api/notifications/user/{user_id}/read-all/`

**Auth:** Required

**Response:** `200 OK`
```json
{
  "message": "All notifications marked as read",
  "count": 5
}
```

### Получить настройки уведомлений

**Endpoint:** `GET /api/notifications/preferences/{user_id}/`

**Auth:** Required

**Response:** `200 OK`
```json
{
  "user_id": 1,
  "email_enabled": true,
  "in_app_enabled": true,
  "push_enabled": false,
  "order_updates": true,
  "review_updates": true,
  "message_updates": true
}
```

### Обновить настройки

**Endpoint:** `PUT /api/notifications/preferences/{user_id}/update/`

**Auth:** Required

**Request:**
```json
{
  "email_enabled": false,
  "in_app_enabled": true,
  "push_enabled": true,
  "order_updates": true,
  "review_updates": false
}
```

**Response:** `200 OK`

## Freelance Service API

### Создать услугу (Gig)

**Endpoint:** `POST /api/gigs/`

**Auth:** Required (freelancer)

**Request:**
```json
{
  "title": "Professional Web Design",
  "description": "I will create a modern website",
  "category_id": 1,
  "main_image": "https://example.com/image.jpg",
  "packages": [
    {
      "type": "basic",
      "price": "50.00",
      "delivery_time": 3,
      "description": "Basic package"
    },
    {
      "type": "standard",
      "price": "100.00",
      "delivery_time": 5,
      "description": "Standard package with revisions"
    }
  ]
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "slug": "professional-web-design",
  "title": "Professional Web Design",
  "seller_id": 1,
  "status": "draft",
  "created_at": "2025-12-04T10:00:00Z"
}
```

### Получить список услуг

**Endpoint:** `GET /api/gigs/`

**Auth:** Optional

**Query Parameters:**
- `category` - ID категории
- `seller_id` - ID продавца
- `status` - active, paused, archived
- `min_price` - минимальная цена
- `max_price` - максимальная цена
- `search` - поиск по названию
- `sort` - rating, price_asc, price_desc, newest

**Response:** `200 OK`
```json
{
  "count": 50,
  "next": "/api/gigs/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "slug": "professional-web-design",
      "title": "Professional Web Design",
      "description": "I will create...",
      "seller": {
        "id": 1,
        "name": "John Doe"
      },
      "category": {
        "id": 1,
        "name": "Web Development"
      },
      "main_image": "https://example.com/image.jpg",
      "rating_average": 4.8,
      "reviews_count": 25,
      "orders_count": 100,
      "starting_price": "50.00"
    }
  ]
}
```

### Получить детали услуги

**Endpoint:** `GET /api/gigs/{id_or_slug}/`

**Auth:** Optional

**Response:** `200 OK`
```json
{
  "id": 1,
  "slug": "professional-web-design",
  "title": "Professional Web Design",
  "description": "Detailed description...",
  "seller": {
    "id": 1,
    "email": "seller@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "profile": {
      "avatar": "https://example.com/avatar.jpg",
      "bio": "Professional web developer"
    }
  },
  "category": {
    "id": 1,
    "name": "Web Development",
    "slug": "web-development"
  },
  "packages": [
    {
      "type": "basic",
      "price": "50.00",
      "delivery_time": 3,
      "description": "Basic package"
    }
  ],
  "main_image": "https://example.com/image.jpg",
  "status": "active",
  "rating_average": 4.8,
  "reviews_count": 25,
  "orders_count": 100,
  "views_count": 500,
  "created_at": "2025-12-01T10:00:00Z"
}
```

### Создать заказ

**Endpoint:** `POST /api/orders/`

**Auth:** Required

**Request:**
```json
{
  "gig_id": 1,
  "package_type": "basic",
  "requirements": "Please use blue colors and modern design"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "gig": {
    "id": 1,
    "title": "Professional Web Design"
  },
  "buyer_id": 2,
  "seller_id": 1,
  "package_type": "basic",
  "price": "50.00",
  "delivery_time": 3,
  "status": "pending",
  "deadline": "2025-12-07T10:00:00Z",
  "created_at": "2025-12-04T10:00:00Z"
}
```

### Получить заказы

**Endpoint:** `GET /api/orders/`

**Auth:** Required

**Query Parameters:**
- `as_buyer` - true/false
- `as_seller` - true/false
- `status` - pending, in_progress, delivered, completed, cancelled

**Response:** `200 OK`
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "gig": {
        "id": 1,
        "title": "Professional Web Design",
        "main_image": "https://example.com/image.jpg"
      },
      "buyer": {
        "id": 2,
        "name": "Jane Smith"
      },
      "seller": {
        "id": 1,
        "name": "John Doe"
      },
      "status": "in_progress",
      "price": "50.00",
      "deadline": "2025-12-07T10:00:00Z",
      "created_at": "2025-12-04T10:00:00Z"
    }
  ]
}
```

### Доставить заказ

**Endpoint:** `POST /api/orders/{order_id}/deliver/`

**Auth:** Required (seller)

**Request:**
```json
{
  "message": "Your order is ready!",
  "file_url": "https://example.com/delivery/file.zip"
}
```

**Response:** `200 OK`

### Завершить заказ

**Endpoint:** `POST /api/orders/{order_id}/complete/`

**Auth:** Required (buyer)

**Response:** `200 OK`

### Создать отзыв

**Endpoint:** `POST /api/reviews/`

**Auth:** Required

**Request:**
```json
{
  "gig_id": 1,
  "order_id": 1,
  "rating": 5,
  "title": "Excellent work!",
  "message": "Very professional and fast delivery"
}
```

**Response:** `201 Created`

### Получить категории

**Endpoint:** `GET /api/categories/`

**Auth:** Optional

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "name": "Web Development",
    "slug": "web-development",
    "icon": "💻",
    "subcategories": [
      {
        "id": 2,
        "name": "Frontend",
        "slug": "frontend"
      }
    ]
  }
]
```

## Content Service API

### Создать канал

**Endpoint:** `POST /api/channels/`

**Auth:** Required

**Request:**
```json
{
  "name": "Tech News",
  "description": "Latest technology news and updates"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "slug": "tech-news",
  "name": "Tech News",
  "description": "Latest technology news and updates",
  "owner_id": 1,
  "created_at": "2025-12-04T10:00:00Z"
}
```

### Получить каналы

**Endpoint:** `GET /api/channels/`

**Auth:** Optional

**Query Parameters:**
- `owner_id` - ID владельца
- `search` - поиск по имени

**Response:** `200 OK`
```json
{
  "count": 20,
  "results": [
    {
      "id": 1,
      "slug": "tech-news",
      "name": "Tech News",
      "description": "Latest technology news",
      "owner": {
        "id": 1,
        "name": "John Doe"
      },
      "members_count": 150,
      "posts_count": 45,
      "created_at": "2025-12-01T10:00:00Z"
    }
  ]
}
```

### Создать пост

**Endpoint:** `POST /api/channels/{channel_slug}/posts/`

**Auth:** Required (member)

**Request:**
```json
{
  "title": "New AI Breakthrough",
  "content": "Scientists have discovered...",
  "image_url": "https://example.com/image.jpg"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "slug": "new-ai-breakthrough",
  "title": "New AI Breakthrough",
  "content": "Scientists have discovered...",
  "author_id": 1,
  "channel": {
    "id": 1,
    "name": "Tech News"
  },
  "image_url": "https://example.com/image.jpg",
  "view_count": 0,
  "like_count": 0,
  "comment_count": 0,
  "created_at": "2025-12-04T10:00:00Z"
}
```

### Получить посты

**Endpoint:** `GET /api/posts/`

**Auth:** Optional

**Query Parameters:**
- `channel` - slug канала
- `author_id` - ID автора
- `search` - поиск по заголовку
- `sort` - newest, popular, trending

**Response:** `200 OK`
```json
{
  "count": 100,
  "results": [
    {
      "id": 1,
      "slug": "new-ai-breakthrough",
      "title": "New AI Breakthrough",
      "content": "Scientists have...",
      "author": {
        "id": 1,
        "name": "John Doe",
        "avatar": "https://example.com/avatar.jpg"
      },
      "channel": {
        "id": 1,
        "name": "Tech News"
      },
      "image_url": "https://example.com/image.jpg",
      "view_count": 250,
      "like_count": 45,
      "comment_count": 12,
      "created_at": "2025-12-04T10:00:00Z"
    }
  ]
}
```

### Добавить лайк

**Endpoint:** `POST /api/likes/`

**Auth:** Required

**Request:**
```json
{
  "post_id": 1
}
```

**Response:** `201 Created`

### Удалить лайк

**Endpoint:** `DELETE /api/likes/{like_id}/`

**Auth:** Required

**Response:** `204 No Content`

### Создать комментарий

**Endpoint:** `POST /api/comments/`

**Auth:** Required

**Request:**
```json
{
  "post_id": 1,
  "content": "Great article!",
  "parent_id": null
}
```

**Response:** `201 Created`

## Marketplace Service API

### Создать товар

**Endpoint:** `POST /api/products/`

**Auth:** Required (seller)

**Request:**
```json
{
  "title": "iPhone 14 Pro",
  "description": "Brand new, sealed",
  "price": "999.00",
  "category_id": 1,
  "condition": "new",
  "quantity": 5,
  "city": "New York",
  "main_image": "https://example.com/iphone.jpg",
  "images": [
    {"image_url": "https://example.com/img1.jpg", "order": 1},
    {"image_url": "https://example.com/img2.jpg", "order": 2}
  ]
}
```

**Response:** `201 Created`

### Получить товары

**Endpoint:** `GET /api/products/`

**Auth:** Optional

**Query Parameters:**
- `category` - ID категории
- `seller_id` - ID продавца
- `condition` - new, used, refurbished
- `min_price` - минимальная цена
- `max_price` - максимальная цена
- `city` - город
- `search` - поиск
- `sort` - price_asc, price_desc, newest

**Response:** `200 OK`
```json
{
  "count": 150,
  "results": [
    {
      "id": 1,
      "slug": "iphone-14-pro",
      "title": "iPhone 14 Pro",
      "description": "Brand new...",
      "price": "999.00",
      "old_price": null,
      "seller": {
        "id": 1,
        "name": "John's Store"
      },
      "category": {
        "id": 1,
        "name": "Electronics"
      },
      "condition": "new",
      "quantity": 5,
      "city": "New York",
      "main_image": "https://example.com/iphone.jpg",
      "views_count": 100,
      "created_at": "2025-12-04T10:00:00Z"
    }
  ]
}
```

### Получить детали товара

**Endpoint:** `GET /api/products/{id_or_slug}/`

**Auth:** Optional

**Response:** `200 OK` (аналогично списку, но с images array)

## Коды ошибок

| Код | Описание |
|-----|----------|
| 200 | OK - Успешный запрос |
| 201 | Created - Ресурс создан |
| 204 | No Content - Успешно, без содержимого |
| 400 | Bad Request - Неверные данные |
| 401 | Unauthorized - Требуется аутентификация |
| 403 | Forbidden - Недостаточно прав |
| 404 | Not Found - Ресурс не найден |
| 429 | Too Many Requests - Rate limit превышен |
| 500 | Internal Server Error - Ошибка сервера |
| 502 | Bad Gateway - Сервис недоступен |
| 504 | Gateway Timeout - Таймаут запроса |

### Примеры ошибок

**400 Bad Request:**
```json
{
  "error": "Validation error",
  "details": {
    "email": ["This field is required"],
    "password": ["Password must be at least 8 characters"]
  }
}
```

**401 Unauthorized:**
```json
{
  "error": "Authentication required",
  "message": "Please provide a valid token"
}
```

**403 Forbidden:**
```json
{
  "error": "Permission denied",
  "message": "You don't have permission to perform this action"
}
```

**429 Too Many Requests:**
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 60,
  "message": "Too many requests. Please try again in 60 seconds"
}
```

## Rate Limiting

API Gateway применяет rate limiting:

- **По умолчанию:** 1000 запросов в минуту на IP адрес
- **При превышении:** HTTP 429 с retry_after в секундах

Headers в ответе:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1638614400
```

## Pagination

Списки используют cursor pagination:

```json
{
  "count": 100,
  "next": "/api/gigs/?cursor=abc123",
  "previous": null,
  "results": [...]
}
```

Query Parameters:
- `limit` - количество элементов (default: 20, max: 100)
- `cursor` - курсор для следующей страницы

## Filtering & Sorting

Большинство list endpoints поддерживают:

**Фильтрация:**
```
GET /api/gigs/?category=1&min_price=50&max_price=200
```

**Сортировка:**
```
GET /api/gigs/?sort=rating
GET /api/gigs/?sort=-created_at  # desc
```

**Поиск:**
```
GET /api/gigs/?search=web+design
```

## WebSocket API

(В разработке)

```javascript
// Подключение к уведомлениям
const ws = new WebSocket('wss://yourdomain.com/ws/notifications/');

ws.onmessage = (event) => {
  const notification = JSON.parse(event.data);
  console.log('New notification:', notification);
};
```

## Postman Collection

Скачайте Postman collection для удобного тестирования:

[Download Postman Collection](../postman/microservices.postman_collection.json)

## См. также

- [README](../README.md)
- [Архитектура](ARCHITECTURE.md)
- [Документация сервисов](services/)
