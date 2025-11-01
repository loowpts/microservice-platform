from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    
    path('', views.post_list, name='post_list'),
    path('create/', views.post_create, name='post_create'),
    path('<slug:post_slug>/', views.post_detail, name='post_detail'),
    path('<slug:post_slug>/update/', views.post_update, name='post_update'),
    path('<slug:post_slug>/delete/', views.post_delete, name='post_delete'),
]
