import requests
import logging
from .proxies import UserProxy
from django.conf import settings


logger = logging.getLogger(__name__)

USER_SERVICE_URL = "http://localhost:8000/api/profile/"

def get_user(user_id):
    """Получить одного пользователя"""
    response = requests.get(f"{USER_SERVICE_URL}{user_id}/")
    if response.status_code == 200:
        return UserProxy.from_api(response.json())
    return None


def get_users_batch(user_ids):
    """Получить несколько пользователей за один запрос"""
    if not user_ids:
        return []
    
    user_ids = list(set(filter(None, user_ids)))
    
    if not user_ids:
        return []
    
    try:
        response = requests.post(
            f"{settings.USER_SERVICE_URL}/api/users/batch/",
            json={"ids": user_ids},
            headers={
                'Authorization': f'Bearer {settings.SERVICE_TOKEN}',
            },
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        
        logger.warning(f"Batch user fetch failed: {response.status_code}")
        return []
        
    except requests.RequestException as e:
        logger.error(f"Error fetching users batch: {e}")
        return []


def verify_user_exists(user_id):
    """Проверить, существует ли пользователь"""
    return get_user(user_id) is not None
