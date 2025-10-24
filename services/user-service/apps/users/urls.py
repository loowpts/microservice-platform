from django.urls import path
from .views import create_user, get_profile, get_profile_detail, update_profile, delete_user, set_role

app_name = 'users'

urlpatterns = [
    path('api/users/', create_user, name='create_user'),
    path('api/profile/', get_profile, name='profile'),
    path('api/profile/<int:pk>/', get_profile_detail, name='profile_detail'),
    path('api/profile/update/', update_profile, name='update_profile'),
    path('api/users/<int:pk>/delete/', delete_user, name='delete_user'),
    path('api/set-role/', set_role, name='set_role'),
]
