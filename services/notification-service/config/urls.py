from django.contrib import admin
from django.urls import path, include
from apps.common.views import health_check

urlpatterns = [
    path('health/', health_check, name='health_check'),
    
    path("admin/", admin.site.urls),

    path('api/notifications/', include('apps.notifications.urls', namespace='notifications')),
    
]
