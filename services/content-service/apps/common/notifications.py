import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

NOTIFICATION_SERVICE_URL = getattr(settings, 'NOTIFICATION_SERVICE_URL', 'http://localhost:8001')


def send_notification(user_id, event, title, message, notification_type='in_app', email_to=None, data=None):
    """
    Отправить уведомление через notification-service
    
    Args:
        user_id: ID пользователя
        event: Тип события (order_created, review_posted, etc)
        title: Заголовок уведомления
        message: Текст уведомления
        notification_type: Тип ('in_app', 'email', 'push')
        email_to: Email для отправки (если type='email')
        data: Дополнительные данные (dict)
        
    Returns:
        int: ID созданного уведомления или None
    """
    if not user_id:
        logger.warning('send_notification called without user_id')
        return None
    
    try:
        response = requests.post(
            f'{NOTIFICATION_SERVICE_URL}/api/notifications/send/',
            json={
                'user_id': user_id,
                'type': notification_type,
                'event': event,
                'title': title,
                'message': message,
                'email_to': email_to,
                'data': data or {}
            },
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        
        if response.status_code == 201:
            return response.json()['notification_id']
        
        logger.warning(f"Failed to send notification: {response.status_code}")
        return None
        
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        return None
