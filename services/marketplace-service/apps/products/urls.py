from django.urls import path
from . import views
app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('my/', views.my_products, name='my_products'),
    path('create/', views.product_create, name='product_create'),
    
    path('<slug:slug>/', views.product_detail, name='product_detail'),
    path('<slug:slug>/update/', views.product_update, name='product_update'),
    path('<slug:slug>/delete/', views.product_delete, name='product_delete')
    
]

