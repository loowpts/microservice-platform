import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

USER_SERVICE_URL = getattr(settings, 'USER_SERVICE_URL', 'http://localhost:8000')


def get_user(user_id):
    """
    Получить данные одного пользователя из user-service
    
    Args:
        user_id: ID пользователя
        
    Returns:
        dict: Данные пользователя или None
    """
    if not user_id:
        return None
    
    try:
        response = requests.get(
            f'{USER_SERVICE_URL}/api/profile/',
            params={'user_id': user_id},
            timeout=5
        )
        
        if response.status_code == 200:
            return response.json()['profile']
        
        logger.warning(f"Failed to get user {user_id}: {response.status_code}")
        return None
        
    except requests.RequestException as e:
        logger.error(f"Error fetching user {user_id}: {e}")
        return None


def get_users_batch(user_ids):
    """
    Получить данные нескольких пользователей одним запросом
    
    Args:
        user_ids: Список ID пользователей
        
    Returns:
        list: Список dict'ов с данными пользователей
    """
    if not user_ids:
        return []
    
    user_ids = list(set(filter(None, user_ids)))
    
    if not user_ids:
        return []
    
    try:
        response = requests.post(
            f'{USER_SERVICE_URL}/api/users/batch/',
            json={'user_ids': user_ids},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()['users']
        
        logger.warning(f"Batch user fetch failed: {response.status_code}")
        return []
        
    except requests.RequestException as e:
        logger.error(f"Error fetching users batch: {e}")
        return []


def verify_user_exists(user_id):
    """
    Проверить, существует ли пользователь
    
    Args:
        user_id: ID пользователя
        
    Returns:
        bool: True если существует, False если нет
    """
    return get_user(user_id) is not None
