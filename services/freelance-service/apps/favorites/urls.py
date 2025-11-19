from django.urls import path
from . import views

app_name = 'favorites'

urlpatterns = [
    
    path('', views.favorite_list, name='favorite_list'),
    path('add/', views.favorite_add, name='favorite_add'),
    path('<int:gig_id>/remove/', views.favorite_remove, name='favorite_remove'),
    path('<int:gig_id>/check/', views.favorite_check, name='favorite_check'),
    
]
