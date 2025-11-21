import json
import logging
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.db.models import Q

from .models import Notification, NotificationPreference
from .tasks import send_email_task

logger = logging.getLogger(__name__)

@require_http_methods(['POST'])
def send_notification(request):
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    
    user_id = data.get('user_id')
    type = data.get('type')
    event = data.get('event')
    title = data.get('title')
    message = data.get('message')
    data_extra = data.get('data', {})
    email_to = data.get('email_to')
    
    if not user_id or not event or not title or not message:
        return JsonResponse({
            'success': False,
            'error': 'Все поля обязательны для заполнения (user_id, event, title, message)'
        }, status=400)

    prefs, _ = NotificationPreference.objects.get_or_create(
        user_id=user_id,
        defaults={'email_enabled': True, 'in_app_enabled': True}
    )
    
    if type == 'email' and not prefs.email_enabled:
        return JsonResponse({
            'success': False,
            'error': 'Email notifications disabled'
        }, status=400)
    if type == 'in_app' and not prefs.in_app_enabled:
        return JsonResponse({
            'success': False,
            'error': 'In-app notifications disabled'
        }, status=400)
    
    notification = Notification.objects.create(
        user_id=user_id,
        type=type,
        event=event,
        title=title,
        message=message,
        data=data_extra,
        email_to=email_to,
        status='pending'
    )
    
    if type == 'email':
        send_email_task.delay(notification.id)
    elif type == 'in_app':
        notification.mark_as_sent()
    
    logger.info(f'Notification created: {notification.id}')
    
    return JsonResponse({
        'success': True,
        'notification_id': notification.id,
        'message': 'Notification created'
    }, status=201)
    
@require_http_methods(['GET'])
def get_user_notifications(request, user_id):
    status = request.GET.get('status')
    type = request.GET.get('type')
    unread_only = request.GET.get('unread_only', 'false').lower() == 'true'
    
    all_notifications = Notification.objects.filter(user_id=user_id)

    if status:
        all_notifications = all_notifications.filter(status=status)
    if type:
        all_notifications = all_notifications.filter(type=type)
    if unread_only:
        all_notifications = all_notifications.filter(read_at__isnull=True)

    all_notifications = all_notifications.order_by('-created_at')

    unread_count = Notification.objects.filter(
        user_id=user_id,
        read_at__isnull=True
    ).count()

    notifications = all_notifications[:50]

    data = [
        {
            'id': n.id,
            'type': n.type,
            'event': n.event,
            'title': n.title,
            'message': n.message,
            'data': n.data,
            'status': n.status,
            'read_at': n.read_at.isoformat() if n.read_at else None,
            'created_at': n.created_at.isoformat(),
        }
        for n in notifications
    ]

    return JsonResponse({
        'success': True,
        'count': len(data),
        'unread_count': unread_count,
        'data': data
    }, status=200)

@require_http_methods(['POST'])
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)
    
    if notification.type != 'in_app':
        return JsonResponse({
            'success': False,
            'error': 'Только уведомления типа in-app можно пометить как прочитанные'
        }, status=400)
    
    notification.mark_as_read()
    
    logger.info(f'Notification marked as read: {notification_id}')
    
    return JsonResponse({
        'success': True,
        'message': 'Notifications marked as read'
    }, status=200)

@require_http_methods(['POST'])
def mark_all_read(request, user_id):
    notifications = Notification.objects.filter(
        user_id=user_id,
        type='in_app',
        read_at__isnull=True
    )
    
    count = notifications.update(
        read_at=timezone.now(),
        status='read'
    )
    
    logger.info(f'Marked {count} notifications as read for user {user_id}')
    
    return JsonResponse({
        'success': True,
        'count': count,
        'message': 'All notifications marked as read'
    }, status=200)
    
@require_http_methods(['PUT'])
def update_preferences(request, user_id):
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    
    prefs, _ = NotificationPreference.objects.get_or_create(user_id=user_id)
    
    for field in ['email_enabled', 'in_app_enabled', 'push_enabled',
                  'order_updates', 'review_updates', 'message_updates']:
        if field in data:
            setattr(prefs, field, data[field])
    
    prefs.save()
    
    logger.info(f'Preferences updated for user {user_id}')
    
    return JsonResponse({
        'success': True,
        'message': 'Preferences updated',
        'preferences': {
            'email_enabled': prefs.email_enabled,
            'in_app_enabled': prefs.in_app_enabled,
            'push_enabled': prefs.push_enabled,
            'order_updates': prefs.order_updates,
            'review_updates': prefs.review_updates,
            'message_updates': prefs.message_updates
        }
    }, status=200)

@require_http_methods(['GET'])
def get_preferences(request, user_id):
    
    prefs, _ = NotificationPreference.objects.get_or_create(user_id=user_id)

    return JsonResponse({
        'success': True,
        'preferences': {
            'email_enabled': prefs.email_enabled,
            'in_app_enabled': prefs.in_app_enabled,
            'push_enabled': prefs.push_enabled,
            'order_updates': prefs.order_updates,
            'review_updates': prefs.review_updates,
            'message_updates': prefs.message_updates
        }
    }, status=200)
