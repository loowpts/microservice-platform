from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    
    path('', views.review_list, name='review_list'),
    path('create/', views.review_create, name='review_create'),
    path('<int:review_id>/update/', views.review_update, name='review_update'),
    path('<int:review_id>/delete/', views.review_delete, name='review_delete'),
    path('<int:review_id>/reply/', views.review_reply_create, name='review_reply_create'),
    path('<int:review_id>/reply/update/', views.review_reply_update, name='review_reply_update'),
    path('<int:review_id>/reply/delete/', views.review_reply_delete, name='review_reply_delete'),

]

