import requests
import logging
import os

logger = logging.getLogger(__name__)

CONTENT_SERVICE_URL = os.getenv('CONTENT_SERVICE_URL', 'http://localhost:8003')
FREELANCE_SERVICE_URL = os.getenv('FREELANCE_SERVICE_URL', 'http://localhost:8002')
MARKETPLACE_SERVICE_URL = os.getenv('MARKETPLACE_SERVICE_URL', 'http://localhost:8004')


def get_user_content_stats(user_id: int) -> dict:
    """Получить статистику контента пользователя"""
    try:
        response = requests.get(
            f'{CONTENT_SERVICE_URL}/api/posts/',
            params={'author_id': user_id},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return {'posts_count': data.get('count', 0)}
    except requests.RequestException as e:
        logger.error(f"Content service error: {e}")
    return {'posts_count': 0}


def get_user_gigs_stats(user_id: int) -> dict:
    """Получить статистику гигов пользователя"""
    try:
        response = requests.get(
            f'{FREELANCE_SERVICE_URL}/api/gigs/my/',
            params={'seller_id': user_id},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return {'gigs_count': data.get('count', 0)}
    except requests.RequestException as e:
        logger.error(f"Freelance service error: {e}")
    return {'gigs_count': 0}


def delete_user_data_cascade(user_id: int) -> bool:
    """
    Каскадное удаление данных пользователя из всех сервисов
    Вызывается при удалении аккаунта
    """
    success = True
    services = [
        (CONTENT_SERVICE_URL, '/api/internal/user-cleanup/'),
        (FREELANCE_SERVICE_URL, '/api/internal/user-cleanup/'),
        (MARKETPLACE_SERVICE_URL, '/api/internal/user-cleanup/'),
    ]

    for service_url, endpoint in services:
        try:
            response = requests.post(
                f'{service_url}{endpoint}',
                json={'user_id': user_id},
                timeout=10
            )
            if response.status_code != 200:
                logger.warning(f"Cleanup failed for {service_url}: {response.status_code}")
                success = False
        except requests.RequestException as e:
            logger.error(f"Cleanup error for {service_url}: {e}")
            success = False

    return success
