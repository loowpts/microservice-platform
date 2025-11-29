FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

# Копируем остальной код
COPY . /app

# Создаём non-root пользователя
RUN useradd -m -u 1000 appuser

# Настраиваем права на entrypoint и назначаем владельца всех файлов
RUN chmod +x /app/entrypoint.sh \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8002

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=config.settings

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \ 
    CMD curl -f http://localhost:8002/health/ || exit 1

ENTRYPOINT [ "/app/entrypoint.sh" ]

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8002", "--workers", "3", "--timeout", "60"]
