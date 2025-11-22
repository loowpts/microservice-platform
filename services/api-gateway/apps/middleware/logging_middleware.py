import logging
import time
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('gateway')


class LoggingMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
        
    def process_request(self, request):
        """Логировать входящий запрос"""
        
        request.start_time = time.time()
        
        ip = self.get_client_ip(request)

        logger.info(
            f'-> {request.method} {request.path} '
            f'from {ip} '
            f'User-Agent: {request.META.get("HTTP_USER_AGENT", "Unknown")}'
        )
        
        return None

    def process_response(self, request, response):
        """Логировать ответ"""
        
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
        logger.info(                                                                                                                              
            f'← {request.method} {request.path} '
            f'{response.status_code} '
            f'({duration:.2f}s)'
        )
        
    def get_client_ip(self, request):
        """Получить IP адресс клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
