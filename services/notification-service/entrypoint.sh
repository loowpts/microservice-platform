#!/bin/bash
set -e

echo "=========================================="
echo "Starting Notification Service"
echo "=========================================="

echo "Creating directories..."
mkdir -p /app/databases /app/staticfiles
echo "✓ Directories created"

echo "Waiting for Redis..."
while ! nc -z ${REDIS_HOST:-redis} ${REDIS_PORT:-6379}; do
    sleep 0.5
done
echo "✓ Redis is ready"

echo "Running migrations..."
python manage.py migrate --noinput
echo "✓ Migrations completed"

echo "Collecting static files..."
python manage.py collectstatic --noinput || true
echo "✓ Static files collected"

echo "=========================================="
echo "Starting application..."
echo "=========================================="

exec "$@"
