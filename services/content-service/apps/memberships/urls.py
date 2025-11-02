from django.urls import path
from . import views

app_name = 'memberships'

urlpatterns = [
    path('', views.member_list, name='member_list'),
    path('join/', views.member_join, name='member_join'),
    path('leave/', views.member_leave, name='member_leave'),
    path('<int:user_id>/role/', views.member_update_role, name='member_update_role'),
    path('<int:user_id>/remove/', views.member_remove, name='member_remove'),
]
