from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('dashboard/', views.analytics_dashboard, name='analytics_dashboard'),
    path('gigs/<slug:slug>/stats/', views.analytics_gig_stats, name='analytics_gig_stats'),
    
    path('revenue-chart/', views.analytics_revenue_chart, name='analytics_revenue_chart'),
    path('compare/', views.analytics_compare, name='analytics_compare'),
    path('export/', views.analytics_export, name='analytics_export'),
]
