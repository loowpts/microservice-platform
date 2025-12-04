# API Gateway Service

## Обзор

API Gateway служит единой точкой входа для всех клиентских запросов в микросервисную платформу. Он отвечает за маршрутизацию запросов к соответствующим микросервисам, аутентификацию, rate limiting и логирование.

## Основная информация

- **Порт:** 8080
- **Framework:** Django 5.2.5 + DRF 3.14.0
- **Язык:** Python 3.11
- **Database:** Redis (для кэша и rate limiting)

## Архитектура

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│        API Gateway :8080            │
│  ┌────────────────────────────────┐ │
│  │   Middleware Stack             │ │
│  │  - CORS                        │ │
│  │  - JWT Authentication          │ │
│  │  - Rate Limiting               │ │
│  │  - Logging                     │ │
│  └────────────────────────────────┘ │
│  ┌────────────────────────────────┐ │
│  │   Router                       │ │
│  │  - URL Pattern Matching        │ │
│  │  - Service Discovery           │ │
│  └────────────────────────────────┘ │
│  ┌────────────────────────────────┐ │
│  │   Proxy Handler                │ │
│  │  - Request Forwarding          │ │
│  │  - Response Handling           │ │
│  └────────────────────────────────┘ │
└──────┬───────┬───────┬──────┬───────┘
       │       │       │      │
       ▼       ▼       ▼      ▼
    [User] [Notif] [Free] [Content] [Market]
```

## Основные функции

### 1. Маршрутизация запросов

Gateway анализирует URL паттерны и перенаправляет запросы на соответствующие микросервисы:

```python
# Правила маршрутизации
/api/auth/*       → User Service
/api/users/*      → User Service
/api/profile/*    → User Service

/api/notifications/* → Notification Service

/api/gigs/*       → Freelance Service
/api/orders/*     → Freelance Service
/api/reviews/*    → Freelance Service
/api/proposals/*  → Freelance Service

/api/posts/*      → Content Service
/api/channels/*   → Content Service
/api/comments/*   → Content Service

/api/products/*   → Marketplace Service
/api/categories/* → Marketplace Service (or Freelance)
```

### 2. JWT Аутентификация

Middleware проверяет JWT токены для защищенных endpoints:

```python
# Формат токена в header
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...

# Публичные endpoints (без токена)
POST /api/auth/login/
POST /api/auth/refresh/
POST /api/users/  # регистрация
GET  /api/health/
```

### 3. Rate Limiting

Ограничение количества запросов с использованием Redis:

```python
# По умолчанию
1000 запросов в минуту на IP адрес

# Настраивается через переменные окружения
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=60  # секунд
```

### 4. Логирование

Централизованное логирование всех запросов:

```python
# Логируется
- Timestamp
- Method (GET, POST, etc.)
- Path
- Status Code
- Response Time
- User ID (если аутентифицирован)
- IP Address
```

## API Endpoints

### Health Check

Проверка статуса всех сервисов:

```http
GET /api/health/
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-04T10:00:00Z",
  "services": {
    "user-service": {
      "status": "healthy",
      "response_time": 0.023
    },
    "notification-service": {
      "status": "healthy",
      "response_time": 0.018
    },
    "freelance-service": {
      "status": "healthy",
      "response_time": 0.031
    },
    "content-service": {
      "status": "healthy",
      "response_time": 0.025
    },
    "marketplace-service": {
      "status": "healthy",
      "response_time": 0.029
    }
  }
}
```

### Прокси запросы

Все остальные запросы проксируются на соответствующие сервисы:

```http
# Примеры
GET  /api/users/           → User Service
POST /api/auth/login/      → User Service
GET  /api/notifications/   → Notification Service
POST /api/gigs/            → Freelance Service
GET  /api/posts/           → Content Service
```

## Структура проекта

```
api-gateway/
├── apps/
│   ├── gateway/
│   │   ├── __init__.py
│   │   ├── urls.py          # Маршруты gateway
│   │   ├── views.py         # proxy_request, health_check
│   │   └── router.py        # Логика маршрутизации
│   └── middleware/
│       ├── __init__.py
│       ├── auth_middleware.py    # JWT проверка
│       ├── logging_middleware.py # Логирование
│       └── rate_limit_middleware.py # Rate limiting
├── config/
│   ├── __init__.py
│   ├── settings.py          # Настройки Django
│   ├── urls.py              # Главные URL
│   ├── wsgi.py
│   └── asgi.py
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── manage.py
└── requirements.txt
```

## Конфигурация

### Переменные окружения

```bash
# Django
DEBUG=False
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/0

# Service URLs
USER_SERVICE_URL=http://user-service:8000
NOTIFICATION_SERVICE_URL=http://notification-service:8001
FREELANCE_SERVICE_URL=http://freelance-service:8002
CONTENT_SERVICE_URL=http://content-service:8003
MARKETPLACE_SERVICE_URL=http://marketplace-service:8004

# Rate Limiting
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=60

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://yourapp.com

# Allowed Hosts
ALLOWED_HOSTS=localhost,127.0.0.1,api_gateway
```

### Docker

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh

EXPOSE 8080

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8080/api/health/ || exit 1

ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8080", "--workers", "3"]
```

**docker-compose.yml:**
```yaml
services:
  api-gateway:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: api_gateway
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      - DEBUG=${DEBUG:-False}
      - SECRET_KEY=${SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
    networks:
      - microservices_network
```

## Middleware

### 1. JWT Authentication Middleware

```python
# apps/middleware/auth_middleware.py

class JWTAuthMiddleware:
    """
    Проверяет JWT токены для защищенных endpoints.
    Публичные endpoints пропускаются.
    """

    PUBLIC_URLS = [
        '/api/auth/login/',
        '/api/auth/refresh/',
        '/api/users/',  # POST только (регистрация)
        '/api/health/',
    ]

    def process_request(self, request):
        # Пропустить публичные endpoints
        if self.is_public_url(request.path):
            return None

        # Извлечь токен
        token = self.get_token_from_header(request)
        if not token:
            return JsonResponse({'error': 'Authentication required'}, status=401)

        # Проверить токен
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=['HS256'])
            request.user_id = payload.get('user_id')
        except jwt.ExpiredSignatureError:
            return JsonResponse({'error': 'Token expired'}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({'error': 'Invalid token'}, status=401)
```

### 2. Rate Limiting Middleware

```python
# apps/middleware/rate_limit_middleware.py

class RateLimitMiddleware:
    """
    Ограничивает количество запросов с IP адреса
    используя Redis для хранения счетчиков.
    """

    def process_request(self, request):
        ip = self.get_client_ip(request)
        key = f'rate_limit:{ip}'

        # Получить текущий счетчик
        count = redis_client.get(key)

        if count and int(count) >= settings.RATE_LIMIT_REQUESTS:
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'retry_after': redis_client.ttl(key)
            }, status=429)

        # Увеличить счетчик
        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, settings.RATE_LIMIT_WINDOW)
        pipe.execute()
```

### 3. Logging Middleware

```python
# apps/middleware/logging_middleware.py

class LoggingMiddleware:
    """
    Логирует все входящие запросы и исходящие ответы.
    """

    def process_request(self, request):
        request.start_time = time.time()

        logger.info(
            f"Request: {request.method} {request.path}",
            extra={
                'ip': self.get_client_ip(request),
                'user_id': getattr(request, 'user_id', None),
            }
        )

    def process_response(self, request, response):
        duration = time.time() - request.start_time

        logger.info(
            f"Response: {response.status_code} in {duration:.3f}s",
            extra={
                'path': request.path,
                'method': request.method,
                'status': response.status_code,
                'duration': duration,
            }
        )

        return response
```

## Обработка ошибок

```python
# Типы ошибок и их обработка

# 401 Unauthorized
- Отсутствует токен
- Невалидный токен
- Истекший токен

# 429 Too Many Requests
- Превышен rate limit

# 502 Bad Gateway
- Целевой сервис недоступен

# 504 Gateway Timeout
- Таймаут запроса к сервису (default: 30s)

# 500 Internal Server Error
- Неожиданная ошибка gateway
```

## Мониторинг

### Метрики

Gateway собирает следующие метрики:

```python
# Request metrics
- Total requests
- Requests per endpoint
- Response times
- Error rates

# Service health
- Service availability
- Service response times

# Rate limiting
- Throttled requests
- Top IPs by request count
```

### Health Check детали

```python
# Проверяемые компоненты
1. Gateway health (200 OK)
2. Redis connection
3. All microservices availability
4. Response times

# Интервалы проверки
- Docker healthcheck: каждые 30s
- Internal monitoring: каждые 10s
```

## Безопасность

### Best Practices

1. **HTTPS Only в Production**
   ```python
   SECURE_SSL_REDIRECT = True
   SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
   ```

2. **CORS настройки**
   ```python
   CORS_ALLOWED_ORIGINS = [
       "https://yourapp.com",
       "https://www.yourapp.com",
   ]
   CORS_ALLOW_CREDENTIALS = True
   ```

3. **Security Headers**
   ```python
   SECURE_BROWSER_XSS_FILTER = True
   SECURE_CONTENT_TYPE_NOSNIFF = True
   X_FRAME_OPTIONS = 'DENY'
   ```

4. **Rate Limiting**
   - Защита от DDoS
   - Ограничение по IP
   - Разные лимиты для разных endpoints

## Производительность

### Оптимизации

1. **Connection Pooling**
   - Переиспользование HTTP соединений
   - Keep-alive connections

2. **Async Processing**
   - Неблокирующие запросы
   - Параллельные health checks

3. **Caching**
   - Redis для кэширования
   - Route mapping cache

4. **Gunicorn Workers**
   ```bash
   # 3 worker процесса
   gunicorn config.wsgi:application --workers 3 --bind 0.0.0.0:8080
   ```

## Масштабирование

### Горизонтальное

```bash
# Запуск нескольких инстансов
docker-compose up -d --scale api-gateway=3

# Требуется load balancer (Nginx)
upstream api_gateway {
    server gateway1:8080;
    server gateway2:8080;
    server gateway3:8080;
}
```

### Load Balancing

```nginx
# Nginx конфигурация
upstream api_gateway {
    least_conn;  # Балансировка по наименьшей нагрузке
    server gateway1:8080;
    server gateway2:8080;
    server gateway3:8080;
}

server {
    listen 80;
    location / {
        proxy_pass http://api_gateway;
    }
}
```

## Разработка

### Локальный запуск

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск сервера
python manage.py runserver 8080

# Или через Gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8080 --reload
```

### Тестирование

```bash
# Unit тесты
pytest apps/gateway/tests/

# Integration тесты
pytest apps/gateway/tests/test_integration.py

# С покрытием
pytest --cov=apps/gateway --cov-report=html
```

### Отладка

```bash
# Включить debug режим
DEBUG=True python manage.py runserver 8080

# Просмотр логов
docker-compose logs -f api-gateway

# Проверка Redis
redis-cli -h localhost -p 6379
> KEYS rate_limit:*
```

## Troubleshooting

### Частые проблемы

**1. Service Unavailable (502)**
```bash
# Проверить статус сервисов
docker-compose ps

# Проверить connectivity
docker-compose exec api-gateway curl http://user-service:8000/api/health/
```

**2. Rate Limit Issues**
```bash
# Сбросить rate limit для IP
redis-cli DEL rate_limit:192.168.1.1

# Проверить настройки
docker-compose exec api-gateway env | grep RATE_LIMIT
```

**3. JWT Token Errors**
```bash
# Проверить JWT_SECRET_KEY одинаковый для Gateway и User Service
docker-compose exec api-gateway env | grep JWT_SECRET_KEY
docker-compose exec user-service env | grep JWT_SECRET_KEY
```

## Roadmap

- [ ] WebSocket поддержка
- [ ] GraphQL gateway
- [ ] Advanced rate limiting (per user, per endpoint)
- [ ] Request/Response transformation
- [ ] API versioning
- [ ] Circuit breaker pattern
- [ ] Distributed tracing integration
- [ ] Metrics export (Prometheus)

## См. также

- [Архитектура системы](../ARCHITECTURE.md)
- [User Service](USER-SERVICE.md)
- [API документация](../API.md)
