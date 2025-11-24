import requests
import logging
from django.conf import settings
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

NOTIFICATION_SERVICE_URL = getattr(settings, 'NOTIFICATION_SERVICE_URL', 'http://localhost:8001')


def get_notification_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["POST"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def send_notification(user_id, event, title, message, notification_type='in_app', email_to=None, data=None):
    """Отправить уведомление через notification-service"""
    
    if not user_id or not event:
        logger.error("user_id and event are required")
        return None
    
    try:
        session = get_notification_session()
        response = session.post(
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
            timeout=5
        )
        
        response.raise_for_status()
        
        notification_id = response.json().get('notification_id')
        logger.info(f"Notification sent successfully: {notification_id}")
        return notification_id
            
    except requests.exceptions.Timeout:
        logger.error(f"Timeout sending notification for user {user_id}, event {event}")
        return None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending notification for user {user_id}: {e}")
        return None
        
    except Exception as e:
        logger.error(f"Unexpected error sending notification: {e}")
        return None
