from django.db import models
from django.utils import timezone

class NOTIFICATION_TYPE_CHOICES(models.TextChoices):
    EMAIL = 'email', 'Email'
    IN_APP = 'in_app', 'In-App'
    PUSH = 'push', 'Push'
    

class NOTIFICATION_STATUS_CHOICES(models.TextChoices):
    PENDING = 'pending', 'Ожидает отправки'
    SENT = 'sent', 'Отправлено'
    FAILED = 'failed', 'Ошибка'
    READ = 'read', 'Прочитано'


class Notification(models.Model):
    user_id = models.IntegerField(db_index=True)
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES, default='in_app')
    status = models.CharField(max_length=20, choices=NOTIFICATION_STATUS_CHOICES, default='pending')
    event = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    message = models.TextField(max_length=2000)
    data = models.JSONField(default=dict, blank=True)
    email_to = models.EmailField(blank=True, null=True)
    email_subject = models.CharField(max_length=200, blank=True)
    email_html = models.TextField(blank=True)
    read_at = models.DateTimeField(blank=True, null=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id', 'status']),
            models.Index(fields=['status'])
        ]
    
    def __str__(self):
        return f'{self.type} - {self.title} (User: {self.user_id})'
    
    def mark_as_read(self):
        if not self.read_at:
            self.read_at = timezone.now()
            self.status = 'read'
            self.save(update_fields=['read_at', 'status', 'updated_at'])
    
    def mark_as_sent(self):
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at', 'updated_at'])
    
    def mark_as_failed(self, error):
        self.status = 'failed'
        self.error_message = str(error)
        self.save(update_fields=['status', 'error_message', 'updated_at'])


class NotificationPreference(models.Model):
    user_id = models.IntegerField(db_index=True, unique=True)
    email_enabled = models.BooleanField(default=True)
    in_app_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)
    order_updates = models.BooleanField(default=True)
    review_updates = models.BooleanField(default=True)
    message_updates = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Настройки уведомлений'
        verbose_name_plural = 'Настройки уведомлений'
        
    def __str__(self):
        return f'Preferences for User: {self.user_id}'
    
    
    
