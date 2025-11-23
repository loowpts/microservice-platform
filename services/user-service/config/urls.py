from django.contrib import admin
from django.urls import path, include
from apps.users.views import health_check

urlpatterns = [
    path('health/', health_check, name='health_check'),
    
    path('admin/', admin.site.urls),
    path('', include('apps.users.urls', namespace='users'))
]
