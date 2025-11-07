import json
import logging
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.db.models import Q

from .models import Favorite
from apps.products.models import Product, ProductImage
from apps.common.api import get_users_batch


logger = logging.getLogger(__name__)


@require_http_methods(['GET'])
def favorite_list(request):
    favorites = Favorite.objects.filter(
        user_id=request.user.id
    ).select_related(
        'product',
        'product__category'
    )
    
    product_ids = [f.product.id for f in favorites]
    
    images = ProductImage.objects.filter(
        product_id__in=product_ids
    ).order_by('product_id', 'order')
    
    images_map = {}
    for image in images:
        if image.product_id not in images_map:
            images_map[image.product_id] = image.image_url
            
    seller_ids = list(set([f.product.seller_id for f in favorites]))
    sellers_data = get_users_batch(seller_ids) if seller_ids else []
    sellers_map = {u['id']: u for u in sellers_data}
    
    data = []
    
    for favorite in favorites:
        product = favorite.product
        
        seller = sellers_map.get(product.seller_id)
        
        image_url = images_map.get(product.id)
        
        favorite_data = {
            'favorite_id': favorite.id,
            'product': {
                'id': product.id,
                'title': product.title,
                'slug': product.slug,
                'price': str(product.price),
                'old_price': str(product.old_price) if product.old_price else None,
                'category': {
                    'id': product.category.id,
                    'name': product.category.name,
                    'slug': product.category.slug
                },
                'condition': product.condition,
                'city': product.city,
                'status': product.status,
                'seller_id': product.seller_id,
                'seller': seller,
                'image_url': image_url,
                'views_count': product.views_count
            },
            'added_at': product.created_at.isoformat()
        }

        data.append(favorite_data)
    
    return JsonResponse({
        'success': True,
        'count': len(data),
        'data': data
    }, status=200)


@require_http_methods(['POST'])
def favorite_toggle(request, slug):
    product = get_object_or_404(Product, slug=slug)
    
    favorite = Favorite.objects.filter(
        user_id=request.user.id,
        product=product
    ).first()
    
    if favorite:
        favorite.delete()
        action = 'removed'
        message = 'Товар удален из избранного'
    else:
        Favorite.objects.create(
            user_id=request.user.id,
            product=product
        )
        
        action = 'added'
        message = 'Товар добавлен в избранное'
        
    
    logger.info(f'Favorite {action}: product {product.id} by user {request.user.id}')
    
    
    return JsonResponse({
        'success': True,
        'action': action,
        'message': message
    }, status=200)
