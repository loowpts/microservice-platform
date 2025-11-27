from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # User Management
    path('api/users/', views.create_user, name='create_user'),
    path('api/users/<int:pk>/delete/', views.delete_user, name='delete_user'),
    path('api/users/batch/', views.get_users_batch, name='get_users_batch'),
    
    # Profile Management
    path('api/profile/', views.get_profile, name='profile'),
    path('api/profile/<int:pk>/', views.get_profile_detail, name='profile_detail'),
    path('api/profile/update/', views.update_profile, name='update_profile'),
    
    # Role Management
    path('api/set-role/', views.set_role, name='set_role'),
    
    # Authentication
    path('api/auth/login/', views.login, name='login'),
    path('api/auth/logout/', views.logout, name='logout'),
    path('api/auth/refresh/', views.refresh_token, name='refresh_token'),
    path('api/auth/verify/', views.verify_token, name='verify_token'),
    path('api/auth/me/', views.get_current_user, name='current_user'),
]
