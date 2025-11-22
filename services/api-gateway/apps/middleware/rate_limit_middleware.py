import logging
from django.core.cache import cache
from django.http import JsonResponse
from django.conf import settings
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('gateway')

class RateLimitMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response
        self.requests_limit = settings.RATE_LIMIT_REQUESTS
        self.window = settings.RATE_LIMIT_WINDOW
        return super().__init__(get_response)
    
    def __call__(self, request: HttpRequest) -> HttpResponse:

        ip = self.get_client_ip(request)
        
        cache_key = f'rate_limit:{ip}'
        
        request_count = cache.get(cache_key, 0)
        
        if request_count >= self.requests_limit:
            logger.warning(f'Rate limit exceeded for {ip}')
            return JsonResponse({
                'success': False,
                'error': f'Превышен лимит запросов. Максимум {self.requests_limit} запросов в {self.window} секунд.'
            }, status=429)

        cache.set(cache_key, request_count + 1, timeout=self.window)
        
        return self.get_response(request)
    
    def get_client_ip(self, request):
        """Получить IP адресс клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    