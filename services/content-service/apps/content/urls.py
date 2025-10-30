from django.urls import path
from . import views

app_name = 'content'

urlpatterns = [
    path('', views.channel_list, name='channel_list'),
    path('create/', views.create_channel, name='create_channel'),
    path('search/', views.search_channel, name='search_channel'),
    path('<slug:slug>/', views.channel_detail, name='channel_detail'),
    path('<slug:slug>/update/', views.update_channel, name='update_channel'),
    path('<slug:slug>/delete/', views.delete_channel, name='delete_channel'),
]
