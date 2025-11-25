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

COPY . /app

RUN mkdir -p /app/logs /app/media /app/staticfiles

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# I don't remember which ports I assigned to applications (update ports)
EXPOSE 8002

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=config.settings

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \ 
    CMD curl -f http://localhosthost:8002/health/ || exit 1

ENTRYPOINT [ "/app/entrypoint.sh" ]

# change ports
CMD [ "gunicorn", 'config.wsgi:application', '--bind', "0.0.0.0:8002", '--workers', "3", "--timeout", "60" ]
