#!/bin/bash

set -e 

echo "=========================================="
echo "Starting Content Service application"
echo "=========================================="

echo "Waiting for PostgreSQL at ${DB_HOST:-content_db}:${DB_PORT:-5432}..."
while ! nc -z ${DB_HOST:-content_db} ${DB_PORT:-5432}; do
    sleep 0.5
done
echo "✓ PostgreSQL is available"

echo "Waiting for Redis at ${REDIS_HOST:-content_redis}:${REDIS_PORT:-6379}..."
while ! nc -z ${REDIS_HOST:-content_redis} ${REDIS_PORT:-6379}; do
    sleep 0.5
done
echo "✓ Redis is available"

echo "Collecting static files..."
python manage.py collectstatic --noinput || true
echo "✓ Static files collected"

# Created superuser
if [ -n "$DJANGO_SUPERUSER_USERNAME"] && [ -n "$DJANGO_SUPERUSER_EMAIL"] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
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
