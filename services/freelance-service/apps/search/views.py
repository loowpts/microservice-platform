import json
import logging
from django.db.models import Q, Min
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from apps.common.api import get_users_batch
from apps.gigs.models import Gig

logger = logging.getLogger(__name__)


@require_http_methods(['GET'])
def search_gigs(request):

    query = request.GET.get('query', '').strip()
    category_slug = request.GET.get('category')
    subcategory_slug = request.GET.get('subcategory')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    max_delivery_time = request.GET.get('max_delivery_time')
    min_rating = request.GET.get('min_rating')
    sort_by = request.GET.get('sort_by', 'relevance')
    
    gigs = Gig.objects.filter(status='active')
    gigs = gigs.select_related('category', 'subcategory').prefetch_related('packages')
    
    if query:
        gigs = gigs.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )
    
    if category_slug:
        gigs = gigs.filter(category__slug=category_slug)
    
    if subcategory_slug:
        gigs = gigs.filter(subcategory__slug=subcategory_slug)
        
    min_price_annotated = False
    
    if min_price:
        try:
            min_price_value = float(min_price)
            if not min_price_annotated:
                gigs = gigs.annotate(min_price_calc=Min('packages__price'))
                min_price_annotated = True
            gigs = gigs.filter(min_price_calc__gte=min_price_value)
        except (ValueError, TypeError):
            logger.warning(f'Invalid min_price: {min_price}')
    
    if max_price:
        try:
            max_price_value = float(max_price)
            if not min_price_annotated:
                gigs = gigs.annotate(min_price_calc=Min('packages__price'))
                min_price_annotated = True
            gigs = gigs.filter(min_price_calc__lte=max_price_value)
        except (ValueError, TypeError):
            logger.warning(f'Invalid max_price: {max_price}')
    
    # Фильтр по максимальному сроку доставки
    if max_delivery_time:
        try:
            max_delivery_value = int(max_delivery_time)
            gigs = gigs.annotate(min_delivery_time=Min('packages__delivery_time'))
            gigs = gigs.filter(min_delivery_time__lte=max_delivery_value)
        except (ValueError, TypeError):
            logger.warning(f'Invalid max_delivery_time: {max_delivery_time}')
    
    # Фильтр по минимальному рейтингу
    if min_rating:
        try:
            min_rating_value = float(min_rating)
            gigs = gigs.filter(rating_average__gte=min_rating_value)
        except (ValueError, TypeError):
            logger.warning(f'Invalid min_rating: {min_rating}')
    
    # Сортировка
    sort_options = {
        'relevance': '-created_at',
        'price_low': 'min_price_calc',
        'price_high': '-min_price_calc',
        'rating': '-rating_average',
        'popular': '-orders_count',
        'newest': '-created_at',
    }
    
    if sort_by in ['price_low', 'price_high'] and not min_price_annotated:
        gigs = gigs.annotate(min_price_calc=Min('packages__price'))
        min_price_annotated = True
    
    sort_field = sort_options.get(sort_by, '-created_at')
    gigs = gigs.order_by(sort_field)
    
    # Убираем дубликаты
    gigs = gigs.distinct()
    
    # Получаем данные продавцов
    seller_ids = [g.seller_id for g in gigs]
    sellers_data = get_users_batch(seller_ids)
    sellers_map = {u['id']: u for u in sellers_data}
    
    # Формируем список результатов
    data = []
    for gig in gigs:
        seller = sellers_map.get(gig.seller_id)
        
        # Получаем минимальную цену
        packages = gig.packages.all()
        min_price_value = None
        if packages:
            prices = [p.price for p in packages]
            min_price_value = float(min(prices)) if prices else None
        
        description = gig.description
        if description and len(description) > 200:
            description = description[:200] + '...'
        
        data.append({
            'id': gig.id,
            'title': gig.title,
            'slug': gig.slug,
            'description': description,
            'main_image': gig.main_image,
            'category': {
                'id': gig.category.id,
                'name': gig.category.name,
                'slug': gig.category.slug,
            } if gig.category else None,
            'subcategory': {
                'id': gig.subcategory.id,
                'name': gig.subcategory.name,
                'slug': gig.subcategory.slug,
            } if gig.subcategory else None,
            'seller_id': gig.seller_id,
            'seller': seller,
            'min_price': min_price_value,
            'rating_average': float(gig.rating_average),
            'reviews_count': gig.reviews_count,
            'orders_count': gig.orders_count,
            'created_at': gig.created_at.isoformat(),
        })
    
    filters_applied = {
        'query': query if query else None,
        'category': category_slug,
        'subcategory': subcategory_slug,
        'min_price': float(min_price) if min_price else None,
        'max_price': float(max_price) if max_price else None,
        'max_delivery_time': int(max_delivery_time) if max_delivery_time else None,
        'min_rating': float(min_rating) if min_rating else None,
        'sort_by': sort_by
    }
    
    logger.info(f'Search: query="{query}", results={len(data)}')
    
    return JsonResponse({
        'success': True,
        'query': query,
        'count': len(data),
        'filters': filters_applied,
        'data': data
    })
