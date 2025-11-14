from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    
    path('api/gigs/', include('apps.gigs.urls', namespace='gigs')),
    # path('api/analytics/', include('apps.analytics.urls', namespace='analytics')),
    path('api/categories/', include('apps.categories.urls', namespace='categories')),
    # path('api/favorites/', include('apps.favorites.urls', namespace='favorites')),
    # path('api/orders/', include('apps.orders.urls', namespace='orders')),
    path('api/portfolio/', include('apps.portfolio.urls', namespace='portfolio')),
    # path('api/proposals/', include('apps.proposals.urls', namespace='proposals')),
    # path('api/reviews/', include('apps.reviews.urls', namespace='reviews')),
    # path('api/search/', include('apps.search.urls', namespace='search')),
]
