#!/bin/bash
set -e

echo "Entrypoint: starting user_service container..."

# Ждём пока БД будет доступна
echo "Waiting for PostgreSQL at ${DB_HOST:-user_db}:${DB_PORT:-5432}..."
until nc -z ${DB_HOST:-user_db} ${DB_PORT:-5432}; do
  sleep 0.5
done
echo "PostgreSQL is available."

# Ждём Redis
echo "Waiting for Redis at ${REDIS_HOST:-user_redis}:${REDIS_PORT:-6379}..."
until nc -z ${REDIS_HOST:-user_redis} ${REDIS_PORT:-6379}; do
  sleep 0.5
done
echo "Redis is available."

# Выполняем миграции (без повторного выполнения в CMD)
echo "Running migrations..."
python manage.py migrate --noinput

# Собираем static (полезно для dev, чтобы staticfiles были в volume)
echo "Collecting static files..."
python manage.py collectstatic --noinput || true

# Создание суперпользователя (если переменные заданы)
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  echo "Ensure superuser exists..."
  python - <<PYCODE
from django.contrib.auth import get_user_model
User = get_user_model()
username = "${DJANGO_SUPERUSER_USERNAME}"
email = "${DJANGO_SUPERUSER_EMAIL}"
password = "${DJANGO_SUPERUSER_PASSWORD}"
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print("Superuser created.")
else:
    print("Superuser already exists.")
PYCODE
fi

# Передаём управление основной команде контейнера
exec "$@"
