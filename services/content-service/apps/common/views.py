from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import connection

@require_http_methods(['GET'])
def health_check(request):
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_status = 'healthy'
    except Exception:
        db_status = 'unhealthy'

    return JsonResponse({
        'status': 'healthy' if db_status == 'healthy' else 'degraded',
        'service': 'content-service',
        'database': db_status
    })
