import json
import logging
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from apps.common.api import get_user, get_users_batch
from apps.common.notifications import send_notification
from apps.gigs.models import Gig
from .models import Favorite

logger = logging.getLogger(__name__)


@require_http_methods(['GET'])
def favorite_list(request):
    
    favorites = Favorite.objects.filter(user_id=request.user.id)
    favorites = favorites.order_by('-created_at').select_related(
        'gig__category', 'gig__subcategory'
    ).prefetch_related('gig__packages')
    
    seller_ids = [f.gig.seller_id for f in favorites]
    sellers_data = get_users_batch(seller_ids)
    sellers_map = {u['id']: u for u in sellers_data}
    
    data = []
    for favorite in favorites:
        gig = favorite.gig
        seller = sellers_map.get(gig.seller_id)
        
        packages = gig.packages.all()
        min_price_value = None
        if packages:
            prices = [p.price for p in packages]
            min_price_value = float(min(prices)) if prices else None

        description = gig.description
        if description and len(description) > 200:
            description = description[:200] + '...'
        
        data.append({
            'favorite_id': favorite.id,
            'gig_id': gig.id,
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
            'added_at': favorite.created_at.isoformat(),
        })
    
    return JsonResponse({
        'success': True,
        'count': len(data),
        'data': data
    })


@require_http_methods(['POST'])
def favorite_add(request):
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    
    gig_id = data.get('gig_id')
    if not gig_id:
        return JsonResponse({
            'success': False,
            'error': 'gig_id is required'
        }, status=400)
    
    gig = get_object_or_404(Gig, id=gig_id, status='active')
    
    if gig.seller_id == request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'Вы не можете добавить свою услугу в избранное',
            'code': 'own_gig'
        }, status=400)
    
    favorite, created = Favorite.objects.get_or_create(
        user_id=request.user.id,
        gig=gig
    )
    
    if not created:
        return JsonResponse({
            'success': False,
            'error': 'Услуга уже в избранном',
            'code': 'already_in_favorites'
        }, status=400)
    
    seller = get_user(gig.seller_id)
    
    packages = gig.packages.all()
    min_price_value = None
    if packages:
        prices = [p.price for p in packages]
        min_price_value = float(min(prices)) if prices else None
    
    description = gig.description
    if description and len(description) > 200:
        description = description[:200] + '...'
    
    response_data = {
        'favorite_id': favorite.id,
        'gig_id': gig.id,
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
        'added_at': favorite.created_at.isoformat(),
    }
    
    logger.info(f'Favorite added: user {request.user.id} -> gig {gig.id}')
    
    return JsonResponse({
        'success': True,
        'message': 'Услуга добавлена в избранное',
        'data': response_data
    }, status=201)


@require_http_methods(['DELETE'])
def favorite_remove(request, gig_id):
    
    favorite = Favorite.objects.filter(
        user_id=request.user.id,
        gig_id=gig_id
    ).first()
    
    if not favorite:
        return JsonResponse({
            'success': False,
            'error': 'Услуга не найдена в избранном'
        }, status=404)
    
    logger.info(f'Favorite removed: user {request.user.id} -> gig {gig_id}')
    favorite.delete()
    
    return JsonResponse({
        'success': True,
        'message': 'Услуга удалена из избранного'
    }, status=200)


@require_http_methods(['GET'])
def favorite_check(request, gig_id):
    
    is_favorite = Favorite.objects.filter(
        user_id=request.user.id,
        gig_id=gig_id
    ).exists()
    
    return JsonResponse({
        'success': True,
        'is_favorite': is_favorite,
        'gig_id': gig_id
    }, status=200)
