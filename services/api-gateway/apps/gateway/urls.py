from django.urls import path, re_path
from . import views
   
app_name = 'gateway'

urlpatterns = [
    
    path('health/', views.health_check, name='health'),
    re_path(r'^api/.*$', views.proxy_request, name='proxy'),
    
]
