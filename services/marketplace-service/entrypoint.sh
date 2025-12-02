#!/bin/bash
set -e

echo "=========================================="
echo "Starting Marketplace Service container..."
echo "=========================================="

# Создание директории для базы данных SQLite
if [ "$DB_ENGINE" = "sqlite" ]; then
    echo "Creating database directory..."
    mkdir -p /app/db
    chmod 755 /app/db
    echo "✓ Database directory ready"
fi

# Ждём PostgreSQL (только если используется PostgreSQL)
if [ "$DB_ENGINE" = "postgresql" ]; then
    echo "Waiting for PostgreSQL at ${DB_HOST:-marketplace_db}:${DB_PORT:-5432}..."
    while ! nc -z ${DB_HOST:-marketplace_db} ${DB_PORT:-5432}; do
        sleep 0.5
    done
    echo "✓ PostgreSQL is available"
fi

# Ждём Redis
echo "Waiting for Redis at ${REDIS_HOST:-marketplace_redis}:${REDIS_PORT:-6379}..."
while ! nc -z ${REDIS_HOST:-marketplace_redis} ${REDIS_PORT:-6379}; do
    sleep 0.5
done
echo "✓ Redis is available"

# Миграции
echo "Running database migrations..."
python manage.py migrate --noinput
echo "✓ Migrations completed"

# Static files
echo "Collecting static files..."
python manage.py collectstatic --noinput || true
echo "✓ Static files collected"

# Создание суперпользователя (опционально)
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Creating superuser..."
    python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
username = "$DJANGO_SUPERUSER_USERNAME"
email = "$DJANGO_SUPERUSER_EMAIL"
password = "$DJANGO_SUPERUSER_PASSWORD"
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print("✓ Superuser created successfully")
else:
    print("✓ Superuser already exists")
EOF
fi

echo "=========================================="
echo "Starting application..."
echo "=========================================="

exec "$@"
