from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_kwargs={'max_retries': 5}
)
def send_email_task(self, notification_id):
    """
    Асинхронная отправка email уведомления

    Автоматически повторяет при ошибке с экспоненциальной задержкой
    """
    from .models import Notification

    try:
        notification = Notification.objects.get(id=notification_id)

        if notification.status == 'sent':
            logger.info(f"Notification {notification_id} already sent")
            return

        # Проверяем наличие email данных
        if not notification.email_to:
            logger.warning(f"No email_to for notification {notification_id}")
            notification.mark_as_failed("No recipient email")
            return

        # Отправка email
        send_mail(
            subject=notification.email_subject or notification.title,
            message=notification.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.email_to],
            html_message=notification.email_html,
            fail_silently=False,
        )

        notification.mark_as_sent()
        logger.info(f"Email sent for notification {notification_id}")

    except Notification.DoesNotExist:
        logger.error(f"Notification {notification_id} not found")

    except Exception as e:
        logger.error(f"Failed to send email for notification {notification_id}: {e}")

        try:
            notification = Notification.objects.get(id=notification_id)
            notification.mark_as_failed(str(e))
        except Notification.DoesNotExist:
            pass

        raise  # Повторить задачу


@shared_task
def send_push_notification_task(notification_id):
    """Отправка push уведомления (Firebase)"""
    # TODO: Реализовать когда будет настроен Firebase
    pass


@shared_task
def cleanup_old_notifications():
    """
    Периодическая очистка старых уведомлений
    Запускать через Celery Beat
    """
    from .models import Notification
    from django.utils import timezone
    from datetime import timedelta

    threshold = timezone.now() - timedelta(days=90)

    deleted, _ = Notification.objects.filter(
        created_at__lt=threshold,
        status__in=['sent', 'read']
    ).delete()

    logger.info(f"Deleted {deleted} old notifications")


@shared_task
def retry_failed_notifications():
    """
    Повторная попытка отправки неудавшихся уведомлений
    Запускать через Celery Beat каждые 15 минут
    """
    from .models import Notification
    from django.utils import timezone
    from datetime import timedelta

    # Уведомления, которые failed менее часа назад
    threshold = timezone.now() - timedelta(hours=1)

    failed = Notification.objects.filter(
        status='failed',
        updated_at__gt=threshold
    )

    for notification in failed:
        if notification.type == 'email':
            send_email_task.delay(notification.id)
        elif notification.type == 'push':
            send_push_notification_task.delay(notification.id)

    logger.info(f"Retrying {failed.count()} failed notifications")
