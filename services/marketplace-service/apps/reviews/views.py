import json
import logging
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.db.models import Q


from .models import Review
from apps.products.models import Product
from apps.common.api import get_user, get_users_batch
from .forms import ReviewForm


logger = logging.getLogger(__name__)

@require_http_methods(['GET'])
def review_list(request, slug):
    product = get_object_or_404(
        Product,
        slug=slug
    )
    
    reviews = product.reviews.all()
    
    author_ids = list({p.author_id for p in reviews})
    authors = get_users_batch(author_ids)
    author_map = {u['id']: u for u in authors}

    data = []
    
    for review in reviews:
        author_data = author_map.get(review.author_id)
        
        data.append({
            'id': review.id,
            'rating': review.rating,
            'comment': review.comment,
            'pros': review.pros,
            'cons': review.cons,
            'author_id': review.author_id,
            'author': {
                'id': author_data['id'],
                'email': author_data.get('email', ''),
                'avatar_url': author_data.get('avatar_url'),
            } if author_data else None,
            'created_at': review.created_at.isoformat()
        })
    
    if reviews:
        average_rating = sum([r.rating for r in reviews]) / len(reviews)
        average_rating = round(average_rating, 1)
    else:
        average_rating = None
    
    return JsonResponse({
        'success': True,
        'product': {
            'id': product.id,
            'title': product.title,
            'slug': product.slug,
        },
        'count': len(reviews),
        'average_rating': average_rating,
        'data': data
    })


@require_http_methods(['POST'])
def review_create(request, slug):
    product = get_object_or_404(
        Product,
        slug=slug
    )
    
    if product.seller_id == request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'Вы не можете оставить отзыв на свой товар',
            'code': 'self_review'
        }, status=400)
        
    if Review.objects.filter(product=product, author_id=request.user.id).exists():
        return JsonResponse({
            'success': False,
            'error': 'Вы уже оставили отзыв на этот товар',
            'code': 'duplicate_review'
        }, status=400)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Невалидный Json',
            'code': 'invalid_json'
        }, status=400)
    
    form = ReviewForm(data)
    
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'error': form.errors
        }, status=400)
        
    review = form.save(commit=False)
    review.product = product
    review.author_id = request.user.id
    review.save()
    
    author_data = get_user(review.author_id)
    
    response_data = ({
        'id': review.id,
        'rating': review.rating,
        'comment': review.comment,
        'pros': review.pros,
        'cons': review.cons,
        'author_id': review.author_id,
        'product': {
            'id': product.id,
            'title': product.title,
            'slug': product.slug,
        },
        'author': {
            'id': author_data['id'],
            'email': author_data.get('email', ''),
            'avatar_url': author_data.get('avatar_url'),
        } if author_data else None,
        'created_at': review.created_at.isoformat(),
    })
    
    logger.info(f'Review created: {review.id} for product {product.id}')
    
    return JsonResponse({
        'success': True,
        'message': 'Отзыв успешно добавлен',
        'data': response_data
        
    }, status=200)
