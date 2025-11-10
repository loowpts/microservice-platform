import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Case, When, Value, IntegerField

from apps.products.models import Product
from apps.common.api import get_users_batch


logger = logging.getLogger(__name__)

@require_http_methods(['GET'])
def product_search(request):
    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()
    city = request.GET.get('city', '').strip()
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    condition = request.GET.get('condition')
    
    if not q:
        return JsonResponse({
            'success': False,
            'error': 'Параметр q обязателен',
            'code': 'missing_query'
        }, status=400)
        
    if len(q) < 2:
        return JsonResponse({
            'success': False,
            'error': 'Запрос должен содержать минимум 2 символа',
            'code': 'query_too_short'
        }, status=400)
    
    try:
        if price_min:
            price_min = float(price_min)
            if price_min < 0:
                return JsonResponse({
                    'success': False,
                    'error': 'Минимальная цена не может быть отрицательной',
                    'code': 'invalid_price_min'
                }, status=400)
        if price_max:
            price_max = float(price_max)
            if price_max < 0:
                return JsonResponse({
                    'success': False,
                    'error': 'Максимальная цена не может быть отрицательной',
                    'code': 'invalid_price_max'
                }, status=400)
                
        if price_min and price_max and price_min > price_max:
            return JsonResponse({
                'success': False,
                'error': 'Минимальная цена не может быть больше максимальной',
                'code': 'invalid_price_range'
            }, status=400)
            
    except (ValueError, TypeError):
        return JsonResponse({
            'success': False,
            'error': 'Неверный формат цены',
            'code': 'invalid_price_format'
        }, status=400)
    
    products = Product.objects.filter(
        status='active'
        ).order_by('-created_at')
        
    products = products.filter(
        Q(title__icontains=q) | Q(description__icontains=q)
    )
    
    if category:
        products = products.filter(category__slug=category)
    if city:
        products = products.filter(city__icontains=city)
    if price_min:
        products = products.filter(price__gte=price_min)
    if price_max:
        products = products.filter(price__lte=price_max)
    if condition:
        products = products.filter(condition=condition)
    
    products = products.annotate(
        title_match=Case(
            When(title__icontains=q, then=Value(0)),
            default=Value(1),
            output_field=IntegerField()
        )
    ).order_by('title_match', '-created_at')
    
    products = products.select_related('category').prefetch_related('additional_images')
    
    if not products.exists():
        logger.info(f'Search performed: "{q}" - found 0 results')
        return JsonResponse({
            'success': True,
            'query': q,
            'count': 0,
            'data': []
        })
    
    seller_ids = list(products.values_list('seller_id', flat=True).distinct())
    sellers = get_users_batch(seller_ids)
    sellers_map = {u['id']: u for u in sellers}
    
    data = []
    for product in products:
        seller = sellers_map.get(product.seller_id)
        image_url = None
        
        if hasattr(product, 'main_image') and product.main_image:
            try:
                image_url = product.main_image.url
            except (AttributeError, ValueError):
                image_url = None
        
        if not image_url and product.additional_images.exists():
            try:
                image_url = product.additional_images.first().image.url
            except (AttributeError, ValueError):
                image_url = None
        
        data.append({
            'id': product.id,
            'title': product.title,
            'slug': product.slug,
            'price': product.price,
            'old_price': product.old_price,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
                'slug': product.category.slug,
            } if product.category else None,
            'condition': product.condition,
            'city': product.city,
            'status': product.status,
            'seller_id': product.seller_id,
            'seller': seller,
            'image_url': image_url,
            'views_count': product.views_count,
            'created_at': product.created_at.isoformat()
        })
    
    logger.info(f'Search performed: "{q}" - found {len(data)} results')
    
    return JsonResponse({
        'success': True,
        'query': q,
        'count': len(data),
        'data': data
    })
