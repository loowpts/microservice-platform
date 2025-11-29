from django.urls import path, include

urlpatterns = [
    path('', include('apps.gateway.urls', namespace='gateway')),
    
]
