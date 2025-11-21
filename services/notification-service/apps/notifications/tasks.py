from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Notification
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_email_task(notification_id):
    """Асинхронная отправка email"""
    try:
        notification = Notification.objects.get(id=notification_id)
        
        send_mail(
            subject=notification.email_subject or notification.title,
            message=notification.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.email_to],
            html_message=notification.email_html if notification.email_html else None,
            fail_silently=False,
        )
        
        notification.mark_as_sent()
        logger.info(f'Email sent: {notification_id}')
        
    except Notification.DoesNotExist:
        logger.error(f'Notification not found: {notification_id}')
        
    except Exception as e:
        try:
            notification = Notification.objects.get(id=notification_id)
            notification.mark_as_failed(str(e))
        except:
            pass
        logger.error(f'Email failed: {notification_id}, error: {e}')
