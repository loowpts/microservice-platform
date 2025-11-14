import json
import logging
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from apps.common.api import get_user, get_users_batch
from apps.orders.models import Order
from .models import Review
from .forms import ReviewForm, ReviewReplyForm

logger = logging.getLogger(__name__)


@require_http_methods(['GET'])
def review_list(request):
    gig_id = request.GET.get('gig_id')
    seller_id = request.GET.get('seller_id')
    min_rating = request.GET.get('min_rating')
    
    reviews = Review.objects.all()
    
    if gig_id:
        reviews = reviews.filter(gig_id=gig_id)
    
    if seller_id:
        try:
            seller_id = int(seller_id)
            reviews = reviews.filter(seller_id=seller_id)
        except ValueError:
            logger.warning(f'Invalid seller_id: {seller_id}')
    
    if min_rating:
        reviews = reviews.filter(rating__gte=min_rating)
    
    reviews = reviews.order_by('-created_at').select_related('gig', 'order').prefetch_related('reply')
    
    buyer_id = [r.buyer_id for r in reviews]
    buyer_data = get_users_batch(buyer_id)
    buyer_maps = {u['id']: u for u in buyer_data}
    
    data = []
    for review in reviews:
        buyer = buyer_maps.get(review.buyer_id)
        has_reply = hasattr(review, 'reply')
        data.append({
            'id': review.id,
            'rating': review.rating,
            'comment': review.comment,
            'communication_rating': review.communication_rating,
            'service_quality_rating': review.service_quality_rating,
            'delivery_rating': review.delivery_rating,
            'gig': {
                'id': review.gig.id,
                'title': review.gig.title,
                'slug': review.gig.slug,
            },
            'order_id': review.order.id,
            'buyer_id': review.buyer_id,
            'buyer': buyer,
            'seller_id': review.seller_id,
            'has_reply': has_reply,
            'reply': {
                'message': review.reply.message,
                'created_at': review.reply.created_at.isoformat()
            } if has_reply else None,
            'created_at': review.created_at.isoformat(),
            'updated_at': review.updated_at.isoformat(),
        })
    
    return JsonResponse({
        'success': True,
        'count': len(data),
        'data': data
    })
    

@require_http_methods(['POST'])
def review_create(request):
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    
    order_id = data.get('order_id')
    if not order_id:
        return JsonResponse({
            'success': False,
            'error': 'Order ID required'
        }, status=400)
        
    order = get_object_or_404(Order, id=order_id)
    
    if order.buyer_id != request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'Это не ваш заказ'
        }, status=403)
        
    if order.status != 'completed':
        return JsonResponse({
            'success': False,
            'error': 'Отзыв можно оставить только на завершенный заказ',
            'code': 'order_not_completed'
        }, status=400)
    
    if Review.objects.filter(order=order).exists():
        return JsonResponse({
            'success': False,
            'error': 'Вы уже оставляли отзыв на этот заказ.',
            'code': 'review_already_exists'
        }, status=400)
    
    form = ReviewForm(data)
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)
    
    review = form.save(commit=False)
    review.order = order
    review.gig = order.gig
    review.buyer_id = request.user.id
    review.seller_id = order.gig.seller_id
    review.save()
    
    buyer = get_user(review.buyer_id)
    response_data = {
        "id": review.id,
        "rating": review.rating,
        "comment": review.comment,
        "communication_rating": review.communication_rating,
        "service_quality_rating": review.service_quality_rating,
        "delivery_rating": review.delivery_rating,
        "order_id": review.order_id,
        "buyer_id": review.buyer_id,
        "buyer": buyer,
        "seller_id": review.seller_id,
        "gig": {
            "id": review.gig.id,
            "title": review.gig.title,
            "slug": review.gig.slug,
        },
        'created_at': review.created_at.isoformat(),
        'updated_at': review.updated_at.isoformat(),
    }
    
    logger.info(f'Review Created: {review.id} for order {order.id}')
    
    return JsonResponse({
        'success': True,
        'message': 'Отзыв успешно добавлен',
        'data': response_data
    }, status=201)

@require_http_methods(['PATCH'])
def review_update(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    
    if review.buyer_id != request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'Это не ваш отзыв'
        }, status=403)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    
    form = ReviewForm(data, instance=review)
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)
    
    review = form.save()
    buyer = get_user(review.buyer_id)
    
    response_data = {
        "id": review.id,
        "rating": review.rating,
        "comment": review.comment,
        "communication_rating": review.communication_rating,
        "service_quality_rating": review.service_quality_rating,
        "delivery_rating": review.delivery_rating,
        "order_id": review.order_id,
        "buyer_id": review.buyer_id,
        "buyer": buyer,
        "seller_id": review.seller_id,
        "gig": {
            "id": review.gig.id,
            "title": review.gig.title,
            "slug": review.gig.slug,
        },
        'created_at': review.created_at.isoformat(),
        'updated_at': review.updated_at.isoformat(),
    }
    
    logger.info(f'Review updated: {review.id}')
    
    return JsonResponse({
        'success': True,
        'message': 'Отзыв успешно обновлен',
        'data': response_data
    }, status=200)
    
@require_http_methods(['DELETE'])
def review_delete(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    
    if review.buyer_id != request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'Вы не можете удалить чужой отзыв.'
        }, status=403)
    
    review_id = review.id
    gig = review.gig
    
    logger.info(f'Review deleted: {review_id}')
    review.delete()
    gig.update_rating()
    
    return JsonResponse({
        'success': True,
        'message': 'Отзыв успешно удален'
    }, status=200)

@require_http_methods(['POST'])
def review_reply_create(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    
    if review.seller_id != request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'Только продавец может ответить на отзыв'
        }, status=403)
    
    if hasattr(review, 'reply'):
        return JsonResponse({
            'success': False,
            'error': 'Вы уже ответили на этот отзыв',
            'code': 'reply_already_exists'
        }, status=400)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    
    form = ReviewReplyForm(data)
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)
    
    reply = form.save(commit=False)
    reply.review = review
    reply.save()
    
    logger.info(f'Reply created: {reply.id} for review {review.id}')
    
    return JsonResponse({
        'success': True,
        'message': 'Ответ успешно добавлен',
        'data': {
            'id': reply.id,
            'message': reply.message,
            'created_at': reply.created_at.isoformat(),
            'updated_at': reply.updated_at.isoformat(),
        },
    }, status=201)

@require_http_methods(['PATCH'])
def review_reply_update(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    
    if not hasattr(review, 'reply'):
        return JsonResponse({
            'success': False,
            'error': 'Ответ не найден'
        }, status=404)
    
    reply = review.reply
    if review.seller_id != request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'Только продавец может редактировать отзыв'
        }, status=403)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON' 
        }, status=400)
    
    form = ReviewReplyForm(data, instance=reply)
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)
    
    reply = form.save()
    
    logger.info(f'Reply updated: {reply.id}')
    
    return JsonResponse({
        'success': True,
        'message': 'Ответ успешно обновлен',
        'data': {
            'id': reply.id,
            'message': reply.message,
            'created_at': reply.created_at.isoformat(),
            'updated_at': reply.updated_at.isoformat(),
        },
    }, status=200)
    
@require_http_methods(['DELETE'])
def review_reply_delete(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    
    if not hasattr(review, 'reply'):
        return JsonResponse({
            'success': False,
            'error': 'Отзыва не существует'
        }, status=404)
    
    reply = review.reply
    if review.seller_id != request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'У вас нет прав для удаления'
        }, status=403)
    
    reply_id = reply.id
    logger.info(f'Reply deleted: {reply_id}')
    reply.delete()
    
    return JsonResponse({
        'success': True,
        'message': 'Ответ успешно удален'
    }, status=200)
