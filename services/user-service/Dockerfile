# Используем один stage для удобства разработки
FROM python:3.11-slim

# Установим рабочую директорию
WORKDIR /app

# Установим системные зависимости (curl/netcat нужны для healthcheck/entrypoint)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    netcat \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости и ставим их
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

# Копируем код
COPY . /app

# Копируем entrypoint и даём права
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Порты
EXPOSE 8001

# Переменные окружения по умолчанию (можно переопределить через .env)
ENV PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=user_service.settings \
    DB_HOST=user_db \
    DB_PORT=5432 \
    REDIS_HOST=user_redis \
    REDIS_PORT=6379

# Healthcheck (использует curl)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8001/health/ || exit 1

# Entrypoint запускает миграции/collectstatic и затем команду контейнера.
ENTRYPOINT ["/app/entrypoint.sh"]

# По умолчанию используем runserver для dev
CMD ["sh", "-c", "python manage.py runserver 0.0.0.0:8001"]
