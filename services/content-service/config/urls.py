from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/channels/', include('apps.content.urls', namespace='content')),
]
