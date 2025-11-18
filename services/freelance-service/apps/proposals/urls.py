from django.urls import path
from . import views

app_name = 'proposals'

urlpatterns = [
    path('', views.proposal_list, name='proposal_list'),
    path('create/', views.proposal_create, name='proposal_create'),
    path('<int:proposal_id>/', views.proposal_detail, name='proposal_detail'),
    path('<int:proposal_id>/accept/', views.proposal_accept, name='proposal_accept'),
    path('<int:proposal_id>/reject/', views.proposal_reject, name='proposal_reject'),
]

