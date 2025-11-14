from django.urls import path
from . import views

app_name = 'portfolio'

urlpatterns = [
    # Portfolio items
    path('', views.portfolio_list, name='portfolio_list'),
    path('my/', views.my_portfolio, name='my_portfolio'),
    path('create/', views.portfolio_create, name='portfolio_create'),
    path('<slug:slug>/', views.portfolio_detail, name='portfolio_detail'),
    path('<slug:slug>/update/', views.portfolio_update, name='portfolio_update'),
    path('<slug:slug>/delete/', views.portfolio_delete, name='portfolio_delete'),
    
    # Portfolio images (галерея)
    path('<slug:slug>/images/add/', views.portfolio_image_add, name='portfolio_image_add'),
    path('<slug:slug>/images/<int:image_id>/update/', views.portfolio_image_update, name='portfolio_image_update'),
    path('<slug:slug>/images/<int:image_id>/delete/', views.portfolio_image_delete, name='portfolio_image_delete'),
]
