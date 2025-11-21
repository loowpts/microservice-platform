from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    
    # Orders URLs
    path('', views.order_list, name='order_list'),
    path('create/', views.order_create, name='order_create'),
    path('<int:order_id>/', views.order_detail, name='order_detail'),
    path('<int:order_id>/status/', views.order_update_status, name='order_update_status'),
    path('<int:order_id>/deliver/', views.order_deliver, name='order_deliver'),
    path('<int:order_id>/complete/', views.order_complete, name='order_complete'),
    path('<int:order_id>/cancel/', views.order_cancel, name='order_cancel'),
    
    # Disputes URLs
    path('<int:order_id>/dispute/create/', views.dispute_create, name='dispute_create'),
    path('disputes/', views.dispute_list, name='dispute_list'),
    path('disputes/<int:dispute_id>/', views.dispute_detail, name='dispute_detail'),
    path('disputes/<int:dispute_id>/message/', views.dispute_add_message, name='dispute_add_message'),
    path('disputes/<int:dispute_id>/resolve/', views.dispute_resolve, name='dispute_resolve'),
    
]

