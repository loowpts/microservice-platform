from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path('api/products', include('apps.products.urls', namespace='products')),
    path('api/categories', include('apps.categories.urls', namespace='categories')),
    path('api/favorites/', include('apps.favorites.urls')),
    path('api/search/', include('apps.search.urls', namespace='search')),
    
]
