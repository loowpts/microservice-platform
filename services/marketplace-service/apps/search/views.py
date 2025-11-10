import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q

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
    
    products = Product.objects.filter(
        status='active'
        ).order_by('-created_at')

    if not q:
        return JsonResponse({
            'success': False,
            'error': 'Параметр q обязателен'
        }, status=400)
        
    if len(q) < 2:
        return JsonResponse({
            'success': False,
            'error': 'Запрос должен содержать минимум 2 символа'
        }, status=400)
        
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
    
    products = products.select_related('category').prefetch_related('additional_images')
    
    products = sorted(
        products,
        key=lambda p :(
            (q.lower() not in p.title.lower()),
            -p.created_at.timestamp()
        )
    )
    
    seller_ids = list({p.seller_id for p in products})
    sellers = get_users_batch(seller_ids)
    sellers_map = {u['id']: u for u in sellers}
    
    data = []
    for product in products:
        seller = sellers_map.get(product.seller_id)
        image_url = None
        
        if hasattr(product, 'main_image') and product.main_image:
            image_url = product.main_image.url
        elif hasattr(product, 'additional_images') and product.additional_images.exists():
            image_url = product.additional_images.first().image.url
        
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
    
    
    logger.info(f'Search performed: {q} - found {len(data)} results')
    
    return JsonResponse({
        'success': True,
        'query': q,
        'count': len(data),
        'data': data
    })
    
