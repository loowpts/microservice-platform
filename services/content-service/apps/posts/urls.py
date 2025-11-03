from django.urls import path
from apps.interactions import views as interaction_views
from apps.comments import views as comment_views
from . import views

app_name = 'posts'

urlpatterns = [
    
    path('', views.post_list, name='post_list'),
    path('create/', views.post_create, name='post_create'),
    path('<slug:post_slug>/', views.post_detail, name='post_detail'),
    path('<slug:post_slug>/update/', views.post_update, name='post_update'),
    path('<slug:post_slug>/delete/', views.post_delete, name='post_delete'),
    
    path('<slug:post_slug>/like/', interaction_views.post_like_toggle, name='post_like_toggle'),
    path('<slug:post_slug>/likes/', interaction_views.post_likes_list, name='post_likes_list'),
    path('<slug:post_slug>/likes/count/', interaction_views.post_likes_count, name='post_likes_count'),
    
    path('<slug:post_slug>/comments/', comment_views.comment_list, name='comment_list'),
    path('<slug:post_slug>/comments/create/', comment_views.comment_create, name='comment_create'),
    path('<slug:post_slug>/comments/<int:comment_id>/', comment_views.comment_update, name='comment_update'),
    path('<slug:post_slug>/comments/<int:comment_id>/delete/', comment_views.comment_delete, name='comment_delete'),
    path('<slug:post_slug>/comments/<int:comment_id>/reply/', comment_views.comment_reply, name='comment_reply'),
]

