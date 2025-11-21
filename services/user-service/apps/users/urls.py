from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('api/users/', views.create_user, name='create_user'),
    path('api/profile/', views.get_profile, name='profile'),
    path('api/profile/<int:pk>/', views.get_profile_detail, name='profile_detail'),
    path('api/profile/update/', views.update_profile, name='update_profile'),
    path('api/users/<int:pk>/delete/', views.delete_user, name='delete_user'),
    path('api/set-role/', views.set_role, name='set_role'),
    
    path('api/auth/login/', views.login, name='login'),
    path('api/auth/logout/', views.logout, name='logout'),
    path('api/auth/refresh/', views.refresh_token, name='refresh_token'),
    path('api/auth/verify/', views.verify_token, name='verify_token'),
    path('api/users/batch/', views.get_users_batch, name='get_users_batch'),
]
