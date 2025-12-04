# Руководство по развертыванию

Это руководство описывает процесс развертывания микросервисной платформы в различных окружениях: локальной разработке, staging и production.

## Содержание

- [Требования](#требования)
- [Локальное развертывание](#локальное-развертывание)
- [Production развертывание](#production-развертывание)
- [Docker Compose](#docker-compose)
- [Kubernetes](#kubernetes)
- [Конфигурация](#конфигурация)
- [Миграции БД](#миграции-бд)
- [Мониторинг](#мониторинг)
- [Backup и восстановление](#backup-и-восстановление)
- [Troubleshooting](#troubleshooting)

## Требования

### Минимальные требования

**Разработка:**
- CPU: 4 ядра
- RAM: 8 GB
- Диск: 20 GB свободного места
- Docker 20.10+
- Docker Compose 2.0+

**Production:**
- CPU: 8+ ядер
- RAM: 16+ GB
- Диск: 100+ GB (SSD рекомендуется)
- Docker 20.10+ или Kubernetes 1.24+
- Load Balancer (Nginx/HAProxy)
- SSL сертификаты

### Программное обеспечение

- **Docker:** 20.10 или выше
- **Docker Compose:** 2.0 или выше
- **Git:** для клонирования репозитория
- **PostgreSQL Client:** для backup/restore (опционально)
- **Redis CLI:** для отладки (опционально)

## Локальное развертывание

### 1. Клонирование репозитория

```bash
git clone https://github.com/loowpts/microservice-platform.git
cd microservice-platform
```

### 2. Настройка переменных окружения

```bash
# Копируем пример
cp .env.example .env

# Редактируем .env файл
nano .env
```

Минимальная конфигурация для разработки:

```bash
# Django Settings
DEBUG=True
SECRET_KEY=dev-secret-key-change-this
JWT_SECRET_KEY=dev-jwt-secret-change-this

# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_USER=postgres
DB_PASSWORD=postgres

# Redis
REDIS_PASSWORD=

# Database Names
USER_DB_NAME=user_service_db
NOTIFICATION_DB_NAME=notification_service_db
FREELANCE_DB_NAME=freelance_service_db
CONTENT_DB_NAME=content_service_db
MARKETPLACE_DB_NAME=marketplace_service_db

# Frontend
FRONTEND_URL=http://localhost:3000

# Allowed Hosts
ALLOWED_HOSTS=localhost,127.0.0.1,api_gateway
```

### 3. Запуск всех сервисов

```bash
# Сборка и запуск
docker-compose up -d --build

# Проверка статуса
docker-compose ps
```

### 4. Инициализация баз данных

```bash
# PostgreSQL автоматически создаст БД из init-databases.sql
# Выполнение миграций для каждого сервиса

docker-compose exec user-service python manage.py migrate
docker-compose exec notification-service python manage.py migrate
docker-compose exec freelance-service python manage.py migrate
docker-compose exec content-service python manage.py migrate
docker-compose exec marketplace-service python manage.py migrate
```

### 5. Создание суперпользователя

```bash
docker-compose exec user-service python manage.py createsuperuser
```

### 6. Сбор статических файлов

```bash
docker-compose exec user-service python manage.py collectstatic --noinput
docker-compose exec notification-service python manage.py collectstatic --noinput
docker-compose exec freelance-service python manage.py collectstatic --noinput
docker-compose exec content-service python manage.py collectstatic --noinput
docker-compose exec marketplace-service python manage.py collectstatic --noinput
docker-compose exec api-gateway python manage.py collectstatic --noinput
```

### 7. Проверка работоспособности

```bash
# Health check всех сервисов
curl http://localhost:8080/api/health/

# Или открыть в браузере
# http://localhost:8080/api/health/
```

Ожидаемый ответ:
```json
{
  "status": "healthy",
  "services": {
    "user-service": {"status": "healthy"},
    "notification-service": {"status": "healthy"},
    "freelance-service": {"status": "healthy"},
    "content-service": {"status": "healthy"},
    "marketplace-service": {"status": "healthy"}
  }
}
```

## Production развертывание

### Подготовка к production

#### 1. Обновление переменных окружения

Создайте `.env.production`:

```bash
# Django Settings
DEBUG=False
SECRET_KEY=SUPER_STRONG_SECRET_KEY_HERE_64_CHARS_MINIMUM
JWT_SECRET_KEY=SUPER_STRONG_JWT_SECRET_KEY_HERE

# Database
POSTGRES_USER=prod_user
POSTGRES_PASSWORD=VERY_STRONG_PASSWORD_HERE
DB_USER=prod_user
DB_PASSWORD=VERY_STRONG_PASSWORD_HERE

# Redis
REDIS_PASSWORD=STRONG_REDIS_PASSWORD

# Database Names (используйте те же имена)
USER_DB_NAME=user_service_db
NOTIFICATION_DB_NAME=notification_service_db
FREELANCE_DB_NAME=freelance_service_db
CONTENT_DB_NAME=content_service_db
MARKETPLACE_DB_NAME=marketplace_service_db

# Email (настройте реальный SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Frontend
FRONTEND_URL=https://yourdomain.com

# Allowed Hosts (добавьте ваш домен)
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,api.yourdomain.com

# CORS
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

#### 2. Генерация сильных паролей

```bash
# SECRET_KEY (Django)
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# JWT_SECRET_KEY
openssl rand -base64 64

# Database passwords
openssl rand -base64 32

# Redis password
openssl rand -base64 32
```

#### 3. Production docker-compose

Создайте `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: microservices_postgres_prod
    restart: always
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=postgres
    ports:
      - "127.0.0.1:5432:5432"  # Только localhost
    volumes:
      - postgres_data_prod:/var/lib/postgresql/data
      - ./backups:/backups  # Для backup
      - ./init-databases.sql:/docker-entrypoint-initdb.d/init-databases.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - microservices_network

  redis:
    image: redis:7-alpine
    container_name: microservices_redis_prod
    restart: always
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
    ports:
      - "127.0.0.1:6379:6379"  # Только localhost
    volumes:
      - redis_data_prod:/data
    healthcheck:
      test: ["CMD", "redis-cli", "--no-auth-warning", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - microservices_network

  api-gateway:
    build:
      context: ./services/api-gateway
      dockerfile: Dockerfile
    container_name: api_gateway_prod
    restart: always
    ports:
      - "127.0.0.1:8080:8080"  # Будет за Nginx
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - USER_SERVICE_URL=http://user-service:8000
      - NOTIFICATION_SERVICE_URL=http://notification-service:8001
      - FREELANCE_SERVICE_URL=http://freelance-service:8002
      - CONTENT_SERVICE_URL=http://content-service:8003
      - MARKETPLACE_SERVICE_URL=http://marketplace-service:8004
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
      - CORS_ALLOWED_ORIGINS=${CORS_ALLOWED_ORIGINS}
    volumes:
      - gateway_static:/app/staticfiles
    depends_on:
      redis:
        condition: service_healthy
    networks:
      - microservices_network
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  user-service:
    build:
      context: ./services/user-service
      dockerfile: Dockerfile
    container_name: user_service_prod
    restart: always
    expose:
      - "8000"
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_DB=${USER_DB_NAME}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/1
      - NOTIFICATION_SERVICE_URL=http://notification-service:8001
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
    volumes:
      - user_media:/app/media
      - user_static:/app/staticfiles
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - microservices_network
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G

  # Остальные сервисы аналогично...

volumes:
  postgres_data_prod:
  redis_data_prod:
  gateway_static:
  user_media:
  user_static:
  notification_static:
  freelance_media:
  freelance_static:
  content_media:
  content_static:
  marketplace_media:
  marketplace_static:

networks:
  microservices_network:
    driver: bridge
```

#### 4. Nginx конфигурация

Создайте `/etc/nginx/sites-available/microservices`:

```nginx
# Upstream для API Gateway
upstream api_gateway {
    least_conn;
    server 127.0.0.1:8080;
    # Для масштабирования добавьте больше серверов:
    # server 127.0.0.1:8081;
    # server 127.0.0.1:8082;
}

# HTTP -> HTTPS редирект
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS сервер
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL сертификаты (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # SSL настройки
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Client body size limit
    client_max_body_size 100M;

    # Logs
    access_log /var/log/nginx/microservices_access.log;
    error_log /var/log/nginx/microservices_error.log;

    # API Gateway
    location /api/ {
        proxy_pass http://api_gateway;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Static files
    location /static/ {
        alias /var/www/microservices/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /var/www/microservices/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Frontend (если есть)
    location / {
        root /var/www/microservices/frontend;
        try_files $uri $uri/ /index.html;
    }
}
```

Активируйте конфигурацию:

```bash
sudo ln -s /etc/nginx/sites-available/microservices /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 5. SSL сертификаты (Let's Encrypt)

```bash
# Установка Certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Получение сертификата
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Автообновление (добавится автоматически в cron)
sudo certbot renew --dry-run
```

#### 6. Запуск production

```bash
# Используя production compose файл
docker-compose -f docker-compose.prod.yml up -d --build

# Миграции
docker-compose -f docker-compose.prod.yml exec user-service python manage.py migrate
docker-compose -f docker-compose.prod.yml exec notification-service python manage.py migrate
docker-compose -f docker-compose.prod.yml exec freelance-service python manage.py migrate
docker-compose -f docker-compose.prod.yml exec content-service python manage.py migrate
docker-compose -f docker-compose.prod.yml exec marketplace-service python manage.py migrate

# Статические файлы
docker-compose -f docker-compose.prod.yml exec api-gateway python manage.py collectstatic --noinput
docker-compose -f docker-compose.prod.yml exec user-service python manage.py collectstatic --noinput
docker-compose -f docker-compose.prod.yml exec notification-service python manage.py collectstatic --noinput
docker-compose -f docker-compose.prod.yml exec freelance-service python manage.py collectstatic --noinput
docker-compose -f docker-compose.prod.yml exec content-service python manage.py collectstatic --noinput
docker-compose -f docker-compose.prod.yml exec marketplace-service python manage.py collectstatic --noinput

# Проверка
curl https://yourdomain.com/api/health/
```

## Миграции БД

### Создание новой миграции

```bash
# В контейнере сервиса
docker-compose exec user-service python manage.py makemigrations
docker-compose exec user-service python manage.py migrate
```

### Откат миграции

```bash
# Откат последней миграции
docker-compose exec user-service python manage.py migrate users 0001_initial

# Просмотр списка миграций
docker-compose exec user-service python manage.py showmigrations
```

### Миграция данных

```bash
# Создание data migration
docker-compose exec user-service python manage.py makemigrations --empty users --name migrate_user_roles
```

## Backup и восстановление

### Backup базы данных

```bash
# Создание директории для backup
mkdir -p backups

# Backup всех баз данных
docker-compose exec postgres pg_dumpall -U postgres > backups/full_backup_$(date +%Y%m%d_%H%M%S).sql

# Backup конкретной БД
docker-compose exec postgres pg_dump -U postgres user_service_db > backups/user_service_$(date +%Y%m%d_%H%M%S).sql
docker-compose exec postgres pg_dump -U postgres notification_service_db > backups/notification_service_$(date +%Y%m%d_%H%M%S).sql
docker-compose exec postgres pg_dump -U postgres freelance_service_db > backups/freelance_service_$(date +%Y%m%d_%H%M%S).sql
docker-compose exec postgres pg_dump -U postgres content_service_db > backups/content_service_$(date +%Y%m%d_%H%M%S).sql
docker-compose exec postgres pg_dump -U postgres marketplace_service_db > backups/marketplace_service_$(date +%Y%m%d_%H%M%S).sql
```

### Автоматический backup

Создайте cron job:

```bash
# Редактируем crontab
crontab -e

# Добавляем задачу (каждый день в 3:00)
0 3 * * * cd /path/to/microservice-platform && docker-compose exec -T postgres pg_dumpall -U postgres > backups/full_backup_$(date +\%Y\%m\%d_\%H\%M\%S).sql
```

### Восстановление базы данных

```bash
# Остановить сервисы
docker-compose stop user-service notification-service freelance-service content-service marketplace-service

# Восстановить все БД
cat backups/full_backup_20251204_030000.sql | docker-compose exec -T postgres psql -U postgres

# Восстановить конкретную БД
cat backups/user_service_20251204_030000.sql | docker-compose exec -T postgres psql -U postgres -d user_service_db

# Запустить сервисы
docker-compose start user-service notification-service freelance-service content-service marketplace-service
```

### Backup медиа файлов

```bash
# Создание архива медиа файлов
docker run --rm -v microservice-platform_user_media:/data -v $(pwd)/backups:/backup alpine tar czf /backup/user_media_$(date +%Y%m%d).tar.gz -C /data .
docker run --rm -v microservice-platform_freelance_media:/data -v $(pwd)/backups:/backup alpine tar czf /backup/freelance_media_$(date +%Y%m%d).tar.gz -C /data .
docker run --rm -v microservice-platform_content_media:/data -v $(pwd)/backups:/backup alpine tar czf /backup/content_media_$(date +%Y%m%d).tar.gz -C /data .
docker run --rm -v microservice-platform_marketplace_media:/data -v $(pwd)/backups:/backup alpine tar czf /backup/marketplace_media_$(date +%Y%m%d).tar.gz -C /data .
```

## Масштабирование

### Горизонтальное масштабирование

```bash
# Запуск нескольких инстансов сервиса
docker-compose up -d --scale user-service=3 --scale freelance-service=2

# Требуется настроить load balancer (Nginx)
```

### Настройка Nginx для load balancing

```nginx
upstream user_service {
    least_conn;
    server user-service-1:8000;
    server user-service-2:8000;
    server user-service-3:8000;
}

location /api/users/ {
    proxy_pass http://user_service;
    # остальные настройки...
}
```

## Мониторинг

### Health checks

```bash
# Проверка всех сервисов
curl http://localhost:8080/api/health/

# Проверка конкретного сервиса
curl http://localhost:8000/api/health/
```

### Логи

```bash
# Просмотр логов всех сервисов
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f user-service

# Последние 100 строк
docker-compose logs --tail=100 user-service

# Логи за последние 10 минут
docker-compose logs --since 10m user-service
```

### Метрики

```bash
# Docker stats
docker stats

# Использование ресурсов конкретного контейнера
docker stats user_service
```

## Troubleshooting

### Сервис не запускается

```bash
# Проверить логи
docker-compose logs user-service

# Проверить конфигурацию
docker-compose config

# Пересобрать образ
docker-compose up -d --build user-service
```

### База данных недоступна

```bash
# Проверить статус PostgreSQL
docker-compose ps postgres

# Подключиться к БД
docker-compose exec postgres psql -U postgres

# Проверить логи
docker-compose logs postgres
```

### Redis недоступен

```bash
# Проверить Redis
docker-compose exec redis redis-cli ping

# С паролем
docker-compose exec redis redis-cli -a your-password ping

# Просмотр ключей
docker-compose exec redis redis-cli -a your-password KEYS '*'
```

### Ошибки миграции

```bash
# Откат и повтор
docker-compose exec user-service python manage.py migrate users zero
docker-compose exec user-service python manage.py migrate

# Fake миграции (если уже применены вручную)
docker-compose exec user-service python manage.py migrate --fake
```

### Проблемы с разрешениями

```bash
# Исправить владельца файлов
sudo chown -R $USER:$USER .

# Исправить разрешения для медиа
docker-compose exec user-service chmod -R 755 /app/media
```

## Безопасность в Production

### Checklist

- [ ] DEBUG=False в production
- [ ] Сильные SECRET_KEY и JWT_SECRET_KEY
- [ ] Сильные пароли для БД и Redis
- [ ] HTTPS через Let's Encrypt
- [ ] Firewall настроен (только 80, 443, 22)
- [ ] PostgreSQL и Redis доступны только localhost
- [ ] Регулярные backup
- [ ] Мониторинг и алерты
- [ ] Rate limiting включен
- [ ] CORS настроен правильно
- [ ] Security headers добавлены
- [ ] Логирование настроено
- [ ] Обновления безопасности применяются

### Firewall (UFW)

```bash
# Установка UFW
sudo apt-get install ufw

# Разрешить SSH
sudo ufw allow 22/tcp

# Разрешить HTTP и HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Включить firewall
sudo ufw enable

# Проверить статус
sudo ufw status
```

## Обновление

### Обновление кода

```bash
# Получить последние изменения
git pull origin main

# Пересобрать и перезапустить
docker-compose up -d --build

# Применить миграции
docker-compose exec user-service python manage.py migrate
# ... для остальных сервисов
```

### Zero-downtime deployment

```bash
# 1. Запустить новые контейнеры параллельно
docker-compose up -d --scale user-service=2 --no-recreate

# 2. Подождать пока новый контейнер станет healthy

# 3. Остановить старый контейнер
docker stop user_service_old

# 4. Удалить старый контейнер
docker rm user_service_old
```

## См. также

- [README](../README.md)
- [Архитектура](ARCHITECTURE.md)
- [API документация](API.md)
- [Разработка](DEVELOPMENT.md)
