from django.conf import settings

# Маппинг путек к сервисам
SERVICE_ROUTES = {
       '/api/auth/': settings.USER_SERVICE_URL,
       '/api/users/': settings.USER_SERVICE_URL,
       '/api/profile/': settings.USER_SERVICE_URL,
       
       '/api/orders/': settings.FREELANCE_SERVICE_URL,
       '/api/gigs/': settings.FREELANCE_SERVICE_URL,
       '/api/reviews/': settings.FREELANCE_SERVICE_URL,
       '/api/proposals/': settings.FREELANCE_SERVICE_URL,
       '/api/favorites/': settings.FREELANCE_SERVICE_URL,
       '/api/portfolios/': settings.FREELANCE_SERVICE_URL,
       '/api/search/': settings.FREELANCE_SERVICE_URL,
       '/api/analytics/': settings.FREELANCE_SERVICE_URL,
       '/api/disputes/': settings.FREELANCE_SERVICE_URL,
       
       '/api/notifications/': settings.NOTIFICATION_SERVICE_URL,
       
       '/api/posts/': settings.CONTENT_SERVICE_URL,
       '/api/categories/': settings.CONTENT_SERVICE_URL,
       '/api/comments/': settings.CONTENT_SERVICE_URL,
}

def get_service_url(path):
    """Определить URL сервиса по пути запроса"""
    
    for route_prefix, service_url in SERVICE_ROUTES.items():
        if path.startswith(route_prefix):
            return service_url
    return None
        
def build_target_url(service_url, path, query_params=None):
    """Построить полный URL для запроса к сервису"""

    target_url = f'{service_url}{path}'
    
    if query_params:
        from urllib.parse import urlencode
        query_string = urlencode(query_params)
        target_url = f'{target_url}?{query_string}'
    
    return target_url
