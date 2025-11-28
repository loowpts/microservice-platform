#!/bin/bash
set -e

echo "=========================================="
echo "Starting API Gateway container..."
echo "=========================================="

# Ждём Redis (API Gateway не использует БД, только Redis)
echo "Waiting for Redis at ${REDIS_HOST:-gateway_redis}:${REDIS_PORT:-6379}..."
while ! nc -z ${REDIS_HOST:-gateway_redis} ${REDIS_PORT:-6379}; do
    sleep 0.5
done
echo "✓ Redis is available"

# Проверяем доступность микросервисов (опционально)
echo "Checking microservices availability..."

# User Service
if nc -z ${USER_SERVICE_HOST:-localhost} ${USER_SERVICE_PORT:-8000} 2>/dev/null; then
    echo "✓ User Service is available"
else
    echo "⚠ User Service is not available yet (this is OK on first start)"
fi

# Notification Service
if nc -z ${NOTIFICATION_SERVICE_HOST:-localhost} ${NOTIFICATION_SERVICE_PORT:-8001} 2>/dev/null; then
    echo "✓ Notification Service is available"
else
    echo "⚠ Notification Service is not available yet (this is OK on first start)"
fi

# Freelance Service
if nc -z ${FREELANCE_SERVICE_HOST:-localhost} ${FREELANCE_SERVICE_PORT:-8002} 2>/dev/null; then
    echo "✓ Freelance Service is available"
else
    echo "⚠ Freelance Service is not available yet (this is OK on first start)"
fi

# Content Service
if nc -z ${CONTENT_SERVICE_HOST:-localhost} ${CONTENT_SERVICE_PORT:-8003} 2>/dev/null; then
    echo "✓ Content Service is available"
else
    echo "⚠ Content Service is not available yet (this is OK on first start)"
fi

# Marketplace Service
if nc -z ${MARKETPLACE_SERVICE_HOST:-localhost} ${MARKETPLACE_SERVICE_PORT:-8004} 2>/dev/null; then
    echo "✓ Marketplace Service is available"
else
    echo "⚠ Marketplace Service is not available yet (this is OK on first start)"
fi

# Static files (API Gateway может не иметь статики, но на всякий случай)
echo "Collecting static files..."
python manage.py collectstatic --noinput || true
echo "✓ Static files collected"

echo "=========================================="
echo "Starting API Gateway..."
echo "Port: 8080"
echo "=========================================="

exec "$@"
