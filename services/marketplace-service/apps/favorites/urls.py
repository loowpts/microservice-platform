from django.urls import path
from . import views

app_name = 'favorites'

urlpatterns = [
    path('', views.favorite_list, name='favorite_list'),
    path('<slug:slug>/favorite/', views.favorite_toggle, name='favorite_toggle'),
]
