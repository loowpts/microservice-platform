from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    
    path('api/notifications/send/', views.send_notification, name='send_notification'),
    path('api/notifications/user/<int:user_id>/', views.get_user_notifications, name='get_user_notifications'),
    path('api/notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('api/notifications/user/<int:user_id>/read-all/', views.mark_all_read, name='mark_all_read'),
    path('api/notifications/preferences/<int:user_id>/', views.get_preferences, name='get_preferences'),
    path('api/notifications/preferences/<int:user_id>/update/', views.update_preferences, name='update_preferences'),
    
]

