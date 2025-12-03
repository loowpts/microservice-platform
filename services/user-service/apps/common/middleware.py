import logging
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from apps.users.models import User

logger = logging.getLogger(__name__)

class JWTAuthenticationMiddleware:
    """
    Middleware для автоматической проверки JWT токенов
    Добавляет authenticated user в request.user если токен валидный
    """

    # Эндпоинты, которые не требуют аутентификации
    PUBLIC_PATHS = [
        '/health/',
        '/api/users/',
        '/api/auth/login/',
        '/api/auth/refresh/',
        '/admin/',  # Админка использует стандартную сессионную аутентификацию
        '/static/',
        '/media/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Для публичных путей не трогаем request.user
        # Позволяем Django стандартной аутентификации работать для /admin/
        if self._is_public_path(request.path):
            # НЕ устанавливаем request.user = None для /admin/
            if not request.path.startswith('/admin/'):
                request.authenticated = False
            return self.get_response(request)
        
        # Извлекаем токен из заголовка
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            request.user = None
            request.authenticated = False
            return self.get_response(request)
        
        token = auth_header.split(' ')[1]
        
        try:
            # Проверяем токен
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            
            user = User.objects.select_related('profile').get(id=user_id)
            
            if not user.is_active:
                logger.warning(f'Attempt to use token for inactive user: {user.email}')
                request.user = None
                request.authenticated = False
                return self.get_response(request)
            
            # Добавляем пользователя в request
            request.user = user
            request.authenticated = True
            request.token = access_token
            
            logger.debug(f"User authenticated: {user.email}")
            
        except (TokenError, InvalidToken) as e:
            logger.warning(f'Invalid token: {str(e)}')
            request.user = None
            request.authenticated = False
        
        except User.DoesNotExist:
            logger.warning(f'User not found for token')
            request.user = None
            request.authenticated = False
        
        except Exception as e:
            logger.error(f'Unexpected error during authentication: {str(e)}')
            request.user = None
            request.authenticated = False
        
        return self.get_response(request)
    
    def _is_public_path(self, path):
        return any(path.startswith(public_path) for public_path in self.PUBLIC_PATHS)


class RequireAuthenticationMiddleware:
    """
    Middleware для принудительной проверки аутентификации
    Блокирует неаутентифицированные запросы к защищенным эндпоинтам
    """
    
    # Эндпоинты, которые ТРЕБУЮТ аутентификации
    PROTECTED_PATHS = [
        '/api/profile/update/',
        '/api/users/',  # кроме POST (регистрация)
        '/api/set-role/',
        '/api/auth/logout/',  # logout требует аутентификации
        '/api/auth/verify/',  # verify требует аутентификации
        # НЕ ДОБАВЛЯЙТЕ СЮДА /api/auth/login/ !!!
    ]
    
    # Методы, которые требуют аутентификации для определенных путей
    PROTECTED_METHODS = {
        '/api/profile/': ['PUT', 'DELETE'],
        '/api/users/': ['GET', 'PUT', 'DELETE'],  # POST (регистрация) не требует
    }
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Пропускаем проверку для админки
        if request.path.startswith('/admin/'):
            return self.get_response(request)
        
        # Пропускаем проверку для статики
        if request.path.startswith(('/static/', '/media/')):
            return self.get_response(request)
        
        # Проверяем, требует ли этот путь аутентификации
        if self._requires_authentication(request):
            if not getattr(request, 'authenticated', False):
                return JsonResponse({
                    'error': 'Authentication required',
                    'detail': 'You must be logged in to access this resource'
                }, status=401)
        
        return self.get_response(request)
    
    def _requires_authentication(self, request):
        """Проверяет, требует ли запрос аутентификации"""
        path = request.path
        method = request.method
        
        # Проверяем защищенные пути
        for protected_path in self.PROTECTED_PATHS:
            if path.startswith(protected_path):
                # Исключение для POST /api/users/ (регистрация)
                if protected_path == '/api/users/' and method == 'POST':
                    return False
                return True
        
        # Проверяем защищенные методы для определенных путей
        for protected_path, methods in self.PROTECTED_METHODS.items():
            if path.startswith(protected_path) and method in methods:
                return True
        
        return False
