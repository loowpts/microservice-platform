import pytest
from django.conf import settings
from unittest.mock import Mock


@pytest.fixture(autouse=True)
def setup_test_environment(settings):
    """Автоматически настраивает окружение для всех тестов"""
    settings.DEBUG = True
    settings.ALLOWED_HOSTS = ['*']
    # Добавляем тестовый middleware
    if 'tests.middleware.TestAuthMiddleware' not in settings.MIDDLEWARE:
        settings.MIDDLEWARE = list(settings.MIDDLEWARE) + ['tests.middleware.TestAuthMiddleware']


@pytest.fixture(autouse=True)
def add_middleware_to_test_client(client):
    """Добавляет тестовый middleware к клиенту"""
    original_get = client.get
    original_post = client.post
    original_put = client.put
    original_patch = client.patch
    original_delete = client.delete

    def wrapped_get(*args, **kwargs):
        kwargs.setdefault('HTTP_AUTHORIZATION', 'Bearer test-token')
        return original_get(*args, **kwargs)

    def wrapped_post(*args, **kwargs):
        kwargs.setdefault('HTTP_AUTHORIZATION', 'Bearer test-token')
        kwargs.setdefault('content_type', 'application/json')
        return original_post(*args, **kwargs)

    def wrapped_put(*args, **kwargs):
        kwargs.setdefault('HTTP_AUTHORIZATION', 'Bearer test-token')
        kwargs.setdefault('content_type', 'application/json')
        return original_put(*args, **kwargs)

    def wrapped_patch(*args, **kwargs):
        kwargs.setdefault('HTTP_AUTHORIZATION', 'Bearer test-token')
        kwargs.setdefault('content_type', 'application/json')
        return original_patch(*args, **kwargs)

    def wrapped_delete(*args, **kwargs):
        kwargs.setdefault('HTTP_AUTHORIZATION', 'Bearer test-token')
        return original_delete(*args, **kwargs)

    client.get = wrapped_get
    client.post = wrapped_post
    client.put = wrapped_put
    client.patch = wrapped_patch
    client.delete = wrapped_delete

    return client
