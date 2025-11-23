from django.contrib import admin
from django.urls import path, include
from apps.posts import views as post_views
from apps.common.views import health_check

urlpatterns = [
    path('health/', health_check, name='health_check'),
    
    path('admin/', admin.site.urls),
    
    path('api/channels/', include('apps.content.urls', namespace='content')),
    
    path('api/channels/<slug:channel_slug>/posts/', include('apps.posts.urls', namespace='posts')),
    path('api/posts/search/', post_views.post_search, name='post_search'),
    
    path('api/channels/<slug:channel_slug>/members/', include('apps.memberships.urls', namespace='memberships')),
    
    path('api/likes/', include('apps.interactions.urls', namespace='interactions')),
]
