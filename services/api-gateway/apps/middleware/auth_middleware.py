import jwt
import logging
from django.http import JsonResponse
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('gateway')

# Пути которые не требуют аутентификации
PUBLIC_PATHS = [
    '/api/auth/login/',
    '/api/auth/register/',
    '/api/auth/refresh/',
    '/api/gigs/',
    '/api/search/',
    '/api/posts/',
    '/health/',
]


def is_public_path(path):
    """Проверить является ли путь публичным"""
    for public_path in PUBLIC_PATHS:
        if path.startswith(public_path):
            return True
    return False


class JWTAuthMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
        
    def __call__(self, request):
        if is_public_path(request.path):
            return self.get_response(request)
        
        # Получить токен из заголовка
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return JsonResponse({
                'success': False,
                'error': 'Требуется аутентификация'
            }, status=401)
        
        if not auth_header.startswith('Bearer '):
            return JsonResponse({
                'success': False,
                'error': 'Неверный формат токена'
            }, status=401)
        
        token = auth_header.split(' ')[1]
        
        # Проверить токен
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )

            request.user_id = payload.get('user_id')
            request.user_email = payload.get('email')
            
            logger.info(f'Authenticated user: {request.user_id}')
            
        except jwt.ExpiredSignatureError:
            return JsonResponse({
                'success': False,
                'error': 'Токен истёк'
            }, status=401)
            
        except jwt.InvalidTokenError as e:
            logger.warning(f'Invalid token: {str(e)}')
            return JsonResponse({
                'success': False,
                'error': 'Неверный токен'
            }, status=401)
        
        return self.get_response(request)
