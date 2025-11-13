from django.urls import path
from . import views
app_name = 'gigs'

urlpatterns = [
    path('', views.gig_list, name='gig_list'),
    path('my/', views.my_gigs, name='my_gigs'),
    path('create/', views.gig_create, name='gig_create'),
    path('<slug:slug>/', views.gig_detail, name='gig_detail'),
    path('<slug:slug>/update/', views.gig_update, name='gig_update'),
    path('<slug:slug>/delete/', views.gig_delete, name='gig_delete'),
    path('<slug:slug>/status/', views.gig_status_update, name='gig_status_update'),
    path('<slug:slug>/packages/create/', views.package_create, name='package_create'),
    path('<slug:slug>/packages/<int:package_id>/update/', views.package_update, name='package_update'),
    path('<slug:slug>/packages/<int:package_id>/delete/', views.package_delete, name='package_delete'),
    
]

