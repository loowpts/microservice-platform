import requests
import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .router import get_service_url, build_target_url

logger = logging.getLogger('gateway')

@csrf_exempt
@require_http_methods(['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def proxy_request(request):
    """Универсальный прокси для всех запросов к микросервисам"""
    
    service_url = get_service_url(request.path)
    
    if not service_url:
        return JsonResponse({
            'success': False,
            'error': 'Service not found'
        }, status=404)
    
    target_url = build_target_url(
        service_url,
        request.path,
        request.GET.dict() if request.GET else None
    )
    
    headers = prepare_headers(request)
    
    body = prepary_body(request)
    
    try:
        response = make_request(
            request.method,
            target_url,
            headers,
            body
        )
        
        return create_response(response)
    
    except requests.ConnectionError:
        logger.info(f'Service unavailable: {service_url}')
        return JsonResponse({
            'success': False,
            'error': 'Сервис времменно недоступен'
        }, status=503)
    
    except requests.Timeout:
        logger.error(f'Service timeout: {service_url}')
        return JsonResponse({
            'success': False,
            'error': 'Превышено время ожидания ответа'
        }, status=504)
    
    except Exception as e:
        logger.error(f'Proxy error: {str(e)}')
        return JsonResponse({
            'success': False,
            'error': 'Внутрення ошибка сервера'
        }, status=500)
        
def prepare_headers(request):
    """Подготовить заголовки для запроса к сервису"""
    
    headers = {}
    
    for key, value in request.headers.items():
        if key.lower() not in ['host', 'connection', 'content-length']:
            headers[key] = value
    
    if 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'
       
    return headers

def prepare_body(request):
    """Подготовить тело запроса"""
    if request.method in ['POST', 'PUT', 'PATCH']:
        return request.body
    return None

def make_request(method, url, headers, body):
    """Выполнить HTTP запрос к сервису"""
    
    kwargs = {
        'headers': headers,
        'timeout': 30
    }
    
    if body:
        kwargs['data'] = body
    
    if method == 'GET':
        return requests.get(url, **kwargs)
    elif method == 'POST':
        return requests.post(url, **kwargs)
    elif method == 'PUT':
        return requests.put(url, **kwargs)
    elif method == 'PATCH':
        return requests.patch(url, **kwargs)
    elif method == 'DELETE':
        return requests.delete(url, **kwargs)

def create_response(response):
    """Создать Django response из requests response"""
    
    # Если ответ пустой
    if not response.content:
        return HttpResponse(
            status=response.status_code,
            content_type='application/json'
        )
    
    # Попробовать распарсить как JSON
    try:
        data = response.json()
        return JsonResponse(
            data,
            status=response.status_code,
            safe=False
        )
    except json.JSONDecodeError:
        # Если не JSON - вернуть как есть
        return HttpResponse(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type', 'text/plain')
        )
        
@require_http_methods(['GET'])
def health_check(request):
    """Проверка здоровья Gateway и всех сервисов"""
    
    from django.conf import settings
    
    services_status = {}
    all_healthy = True
    
    # Проверить каждый сервис
    services = {
        'user-service': settings.USER_SERVICE_URL,
        'freelance-service': settings.FREELANCE_SERVICE_URL,
        'notification-service': settings.NOTIFICATION_SERVICE_URL,
        'content-service': settings.CONTENT_SERVICE_URL,
    }
    
    for service_name, service_url in services.items():
        try:
            response = requests.get(
                f'{service_url}/api/health/',
                timeout=5
            )
            services_status[service_name] = {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'response_time': response.elapsed.total_seconds()
            }
        except Exception as e:
            services_status[service_name] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            all_healthy = False
    
    return JsonResponse({
        'status': 'healthy' if all_healthy else 'degraded',
        'gateway': 'healthy',
        'services': services_status
    }, status=200 if all_healthy else 503)
