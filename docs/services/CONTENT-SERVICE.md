# Content Service

## Обзор

Content Service управляет созданием и управлением социального контента платформы: каналы, посты, комментарии, лайки и членство. Сервис предоставляет возможность пользователям создавать каналы, публиковать контент и взаимодействовать с контентом других пользователей.

## Основная информация

- **Порт:** 8003
- **Framework:** Django 5.2.5 + DRF 3.14.0
- **Язык:** Python 3.11
- **Database:** PostgreSQL
- **Cache:** Redis
- **Apps:** content (channels), posts, comments, interactions, memberships

## Архитектура

```
┌──────────────────────────────────────┐
│    Content Service :8003             │
├──────────────────────────────────────┤
│  REST API Layer:                     │
│  - /api/channels/                    │
│  - /api/posts/                       │
│  - /api/comments/                    │
│  - /api/interactions/                │
│  - /api/memberships/                 │
│                                      │
│  Models:                             │
│  - Channel, ChannelMember           │
│  - Post, Like                        │
│  - Comment                           │
│  - Interaction                       │
└──────────────────────────────────────┘
         │
         ▼
    PostgreSQL (content_service_db)
```

## Структура проекта

```
content-service/
├── apps/
│   ├── content/
│   │   ├── models.py          # Channel, ChannelMember
│   │   ├── views.py           # API views
│   │   ├── serializers.py      # DRF serializers
│   │   ├── urls.py
│   │   └── tests.py
│   ├── posts/
│   │   ├── models.py          # Post
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── tests.py
│   ├── comments/
│   │   ├── models.py          # Comment
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── tests.py
│   ├── interactions/
│   │   ├── models.py          # Like, View
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tests.py
│   ├── memberships/
│   │   ├── models.py          # ChannelMember
│   │   ├── views.py
│   │   └── urls.py
│   ├── common/
│   │   └── utils.py           # Вспомогательные функции
│   └── __init__.py
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── tests/
│   └── test_models/
│   └── test_views/
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Модели данных

### Channel (Канал)

| Поле | Тип | Описание |
|------|-----|---------|
| id | Integer | Первичный ключ |
| name | CharField | Название канала (unique, макс. 100 символов) |
| slug | CharField | URL-friendly ID (unique) |
| description | TextField | Описание канала |
| owner_id | Integer | ID владельца канала |
| created_at | DateTime | Дата создания |
| updated_at | DateTime | Дата обновления |

**Методы:**
- `get_members_count()` - получить количество участников
- `get_posts_count()` - получить количество постов
- `is_member(user_id)` - проверить является ли пользователь членом

### ChannelMember (Член канала)

| Поле | Тип | Описание |
|------|-----|---------|
| id | Integer | Первичный ключ |
| channel | ForeignKey | Связь с Channel |
| user_id | Integer | ID пользователя |
| role | CharField | Роль (owner, admin, moderator, member) |
| joined_at | DateTime | Дата присоединения |

**Roles:**
- owner - владелец канала
- admin - администратор
- moderator - модератор
- member - обычный участник

### Post (Пост)

| Поле | Тип | Описание |
|------|-----|---------|
| id | Integer | Первичный ключ |
| channel | ForeignKey | Связь с Channel |
| author_id | Integer | ID автора |
| title | CharField | Название поста (unique, макс. 200 символов) |
| slug | CharField | URL-friendly ID |
| content | TextField | Содержание поста |
| image_url | URLField | URL изображения поста |
| view_count | PositiveInteger | Количество просмотров |
| like_count | PositiveInteger | Количество лайков |
| comment_count | PositiveInteger | Количество комментариев |
| created_at | DateTime | Дата создания |
| updated_at | DateTime | Дата обновления |

**Методы:**
- `increment_views()` - увеличить счетчик просмотров
- `update_like_count()` - обновить счетчик лайков
- `update_comment_count()` - обновить счетчик комментариев
- `can_edit(user_id, role)` - проверить может ли пользователь редактировать пост

### Comment (Комментарий)

| Поле | Тип | Описание |
|------|-----|---------|
| id | Integer | Первичный ключ |
| post | ForeignKey | Связь с Post |
| author_id | Integer | ID автора комментария |
| content | TextField | Текст комментария |
| parent | ForeignKey | Для вложенных комментариев (self-relation) |
| created_at | DateTime | Дата создания |

**Методы:**
- `get_replies()` - получить ответы на комментарий

### Like (Лайк) / Interaction

| Поле | Тип | Описание |
|------|-----|---------|
| id | Integer | Первичный ключ |
| user_id | Integer | ID пользователя |
| post | ForeignKey | Связь с Post |
| type | CharField | Тип взаимодействия (like, bookmark) |
| created_at | DateTime | Дата создания |

## API Endpoints

### Каналы (Channels)

#### Получить все каналы

```http
GET /api/channels/?page=1&search=design&ordering=-created_at
```

**Query Parameters:**
- `page` (int) - номер страницы
- `search` (string) - поиск по названию
- `ordering` - сортировка (-created_at, members_count)

**Response (200 OK):**
```json
{
  "count": 45,
  "next": "http://localhost:8003/api/channels/?page=2",
  "results": [
    {
      "id": 1,
      "name": "Web Design Tips",
      "slug": "web-design-tips",
      "description": "Share and discuss web design tips and tricks",
      "owner": {
        "id": 5,
        "email": "user@example.com",
        "first_name": "John"
      },
      "members_count": 123,
      "posts_count": 45,
      "created_at": "2025-12-01T10:00:00Z"
    }
  ]
}
```

#### Создать канал

```http
POST /api/channels/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "Photography Lovers",
  "description": "A community for photography enthusiasts"
}
```

**Response (201 Created):**
```json
{
  "id": 2,
  "name": "Photography Lovers",
  "slug": "photography-lovers",
  "description": "A community for photography enthusiasts",
  "owner_id": 5,
  "created_at": "2025-12-04T10:00:00Z"
}
```

#### Получить канал

```http
GET /api/channels/{id}/
```

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "Web Design Tips",
  "slug": "web-design-tips",
  "description": "Share and discuss web design tips and tricks",
  "owner": {...},
  "members_count": 123,
  "posts_count": 45,
  "current_user_role": "member",
  "created_at": "2025-12-01T10:00:00Z"
}
```

#### Обновить канал

```http
PATCH /api/channels/{id}/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "Updated Channel Name",
  "description": "Updated description"
}
```

#### Удалить канал

```http
DELETE /api/channels/{id}/
Authorization: Bearer {access_token}
```

### Членство в каналах (Memberships)

#### Присоединиться к каналу

```http
POST /api/channels/{id}/join/
Authorization: Bearer {access_token}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "user_id": 5,
  "channel_id": 1,
  "role": "member",
  "joined_at": "2025-12-04T10:00:00Z"
}
```

#### Покинуть канал

```http
POST /api/channels/{id}/leave/
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "message": "Successfully left the channel"
}
```

#### Получить членов канала

```http
GET /api/channels/{id}/members/?page=1&role=member
```

**Response (200 OK):**
```json
{
  "count": 123,
  "results": [
    {
      "id": 1,
      "user": {
        "id": 5,
        "email": "user@example.com",
        "first_name": "John"
      },
      "role": "member",
      "joined_at": "2025-12-01T10:00:00Z"
    }
  ]
}
```

#### Изменить роль члена (только администраторы)

```http
PATCH /api/channels/{id}/members/{member_id}/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "role": "moderator"
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "user_id": 5,
  "role": "moderator"
}
```

#### Удалить члена из канала

```http
DELETE /api/channels/{id}/members/{member_id}/
Authorization: Bearer {access_token}
```

**Response (204 No Content)**

### Посты (Posts)

#### Получить посты канала

```http
GET /api/channels/{channel_id}/posts/?page=1&ordering=-created_at
Authorization: Bearer {access_token}
```

**Query Parameters:**
- `page` (int) - номер страницы
- `ordering` - сортировка (-created_at, -view_count, -like_count)

**Response (200 OK):**
```json
{
  "count": 45,
  "results": [
    {
      "id": 1,
      "channel_id": 1,
      "author": {
        "id": 5,
        "first_name": "John"
      },
      "title": "Tips for Responsive Design",
      "slug": "tips-for-responsive-design",
      "content": "Here are some tips...",
      "image_url": "https://...",
      "view_count": 250,
      "like_count": 45,
      "comment_count": 12,
      "can_edit": true,
      "created_at": "2025-12-04T10:00:00Z"
    }
  ]
}
```

#### Создать пост

```http
POST /api/channels/{channel_id}/posts/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "title": "My Design Tips",
  "content": "Here are my best design tips...",
  "image_url": "https://..."
}
```

**Response (201 Created):**
```json
{
  "id": 2,
  "channel_id": 1,
  "author_id": 5,
  "title": "My Design Tips",
  "slug": "my-design-tips",
  "content": "Here are my best design tips...",
  "created_at": "2025-12-04T10:00:00Z"
}
```

#### Получить пост

```http
GET /api/channels/{channel_id}/posts/{id}/
```

**Response (200 OK):**
```json
{
  "id": 1,
  "channel_id": 1,
  "author": {...},
  "title": "Tips for Responsive Design",
  "content": "Here are some tips...",
  "view_count": 251,
  "like_count": 45,
  "comment_count": 12,
  "is_liked": false,
  "created_at": "2025-12-04T10:00:00Z"
}
```

#### Обновить пост

```http
PATCH /api/channels/{channel_id}/posts/{id}/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "title": "Updated title",
  "content": "Updated content"
}
```

#### Удалить пост

```http
DELETE /api/channels/{channel_id}/posts/{id}/
Authorization: Bearer {access_token}
```

### Комментарии (Comments)

#### Получить комментарии поста

```http
GET /api/posts/{post_id}/comments/?page=1&ordering=created_at
```

**Response (200 OK):**
```json
{
  "count": 12,
  "results": [
    {
      "id": 1,
      "post_id": 1,
      "author": {
        "id": 6,
        "first_name": "Jane"
      },
      "content": "Great tips!",
      "replies_count": 2,
      "created_at": "2025-12-04T10:00:00Z"
    }
  ]
}
```

#### Создать комментарий

```http
POST /api/posts/{post_id}/comments/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "content": "This is a great post!",
  "parent_id": null
}
```

**Response (201 Created):**
```json
{
  "id": 2,
  "post_id": 1,
  "author_id": 5,
  "content": "This is a great post!",
  "created_at": "2025-12-04T10:00:00Z"
}
```

#### Создать ответ на комментарий

```http
POST /api/posts/{post_id}/comments/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "content": "Thanks for the feedback!",
  "parent_id": 1
}
```

#### Получить ответы на комментарий

```http
GET /api/posts/{post_id}/comments/{comment_id}/replies/
```

**Response (200 OK):**
```json
{
  "count": 2,
  "results": [...]
}
```

#### Удалить комментарий

```http
DELETE /api/posts/{post_id}/comments/{id}/
Authorization: Bearer {access_token}
```

### Взаимодействия (Interactions)

#### Лайкнуть пост

```http
POST /api/posts/{id}/like/
Authorization: Bearer {access_token}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "user_id": 5,
  "post_id": 1,
  "type": "like",
  "created_at": "2025-12-04T10:00:00Z"
}
```

#### Убрать лайк

```http
DELETE /api/posts/{id}/like/
Authorization: Bearer {access_token}
```

**Response (204 No Content)**

#### Добавить в закладки

```http
POST /api/posts/{id}/bookmark/
Authorization: Bearer {access_token}
```

**Response (201 Created):**
```json
{
  "id": 2,
  "user_id": 5,
  "post_id": 1,
  "type": "bookmark",
  "created_at": "2025-12-04T10:00:00Z"
}
```

## Конфигурация

### Переменные окружения

```bash
# Django
DEBUG=False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1,content-service

# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=content_service_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/5

# Services
USER_SERVICE_URL=http://user-service:8000
NOTIFICATION_SERVICE_URL=http://notification-service:8001

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

EXPOSE 8003

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8003/api/health/ || exit 1

ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8003", "--workers", "3"]
```

## Примеры использования

### Python пример

```python
import requests

BASE_URL = 'http://localhost:8003'
access_token = 'your_token'
headers = {'Authorization': f'Bearer {access_token}'}

# Создать канал
channel_data = {
    'name': 'Web Design Community',
    'description': 'Share your web design work'
}
response = requests.post(
    f'{BASE_URL}/api/channels/',
    json=channel_data,
    headers=headers
)
channel = response.json()
print(f"Channel created: {channel['id']}")

# Присоединиться к каналу
response = requests.post(
    f'{BASE_URL}/api/channels/1/join/',
    headers=headers
)

# Создать пост
post_data = {
    'title': 'My Latest Design',
    'content': 'Check out my latest web design...',
    'image_url': 'https://...'
}
response = requests.post(
    f'{BASE_URL}/api/channels/1/posts/',
    json=post_data,
    headers=headers
)
post = response.json()
print(f"Post created: {post['id']}")

# Лайкнуть пост
response = requests.post(
    f'{BASE_URL}/api/posts/1/like/',
    headers=headers
)
print("Post liked!")

# Добавить комментарий
comment_data = {'content': 'Great design!'}
response = requests.post(
    f'{BASE_URL}/api/posts/1/comments/',
    json=comment_data,
    headers=headers
)
print("Comment added!")
```

### JavaScript пример

```javascript
const BASE_URL = 'http://localhost:8003';
const ACCESS_TOKEN = localStorage.getItem('access_token');

const headers = {
  'Authorization': `Bearer ${ACCESS_TOKEN}`,
  'Content-Type': 'application/json'
};

// Получить каналы
async function getChannels() {
  const response = await fetch(`${BASE_URL}/api/channels/`);
  return await response.json();
}

// Получить посты канала
async function getChannelPosts(channelId) {
  const response = await fetch(
    `${BASE_URL}/api/channels/${channelId}/posts/`
  );
  return await response.json();
}

// Создать пост
async function createPost(channelId, title, content) {
  const response = await fetch(
    `${BASE_URL}/api/channels/${channelId}/posts/`,
    {
      method: 'POST',
      headers,
      body: JSON.stringify({ title, content })
    }
  );
  return await response.json();
}

// Лайкнуть пост
async function likePost(postId) {
  const response = await fetch(
    `${BASE_URL}/api/posts/${postId}/like/`,
    { method: 'POST', headers }
  );
  return response.ok;
}

// Использование
getChannels().then(data => {
  console.log(`Found ${data.count} channels`);
  if (data.results.length > 0) {
    return getChannelPosts(data.results[0].id);
  }
}).then(posts => {
  console.log(`Found ${posts.count} posts`);
});
```

## Тестирование

```bash
# Запуск тестов
python manage.py test apps.content

# Тесты с покрытием
coverage run --source='apps' manage.py test
coverage report
coverage html
```

## Безопасность

1. **Модерация контента** - контент может быть отмечен как неприемлемый
2. **Ограничения доступа** - роли контролируют кто может редактировать/удалять
3. **Rate limiting** - лимит на количество постов/комментариев
4. **Spam protection** - автоматическое определение спама

## Производительность

1. **Кэширование** - посты кэшируются в Redis
2. **Индексы БД** - индексы на часто используемые поля
3. **Pagination** - постраничная выдача результатов
4. **Асинхронные обновления** - счетчики обновляются асинхронно

## Troubleshooting

```bash
# Проверить логи
docker-compose logs content-service

# Миграции БД
docker-compose exec content-service python manage.py migrate

# Проверить состояние Redis
redis-cli -n 5 INFO
```

## Roadmap

- [ ] Real-time notifications для новых комментариев
- [ ] Video posts support
- [ ] Hashtag support
- [ ] Advanced filtering и sorting
- [ ] Content moderation dashboard

## См. также

- [User Service](USER-SERVICE.md)
- [Notification Service](NOTIFICATION-SERVICE.md)
- [API Gateway Service](API-GATEWAY.md)
- [Архитектура системы](../ARCHITECTURE.md)
