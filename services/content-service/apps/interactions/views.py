import json
import logging
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib.contenttypes.models import ContentType

from apps.posts.models import Post
from apps.common.api import get_users_batch
from .models import Like

logger = logging.getLogger(__name__)


@require_http_methods(['POST'])
def post_like_toggle(request, channel_slug, post_slug):
    
    post = get_object_or_404(
        Post,
        slug=post_slug,
        channel__slug=channel_slug
    )
    
    content_type = ContentType.objects.get_for_model(Post)
    
    existing_like = Like.objects.filter(
        user_id=request.user.id,
        content_type=content_type,
        object_id=post.id
    ).first()
    
    if existing_like:
        existing_like.delete()
        
        logger.info(f'Post unliked: user {request.user.id} unliked post {post.id}')
        
        return JsonResponse({
            'success': True,
            'message': 'Лайк убран',
            'is_liked': False
            
        }, status=200)
        
    else:
        
        like = Like.objects.create(
            user_id=request.user.id,
            content_type=content_type,
            object_id=post.id
        )
    
    logger.info(f'Like created: user {request.user.id} liked {content_type} {post.id}')

    return JsonResponse({
        'success': True,
        'message': 'Лайк поставлен',
        'is_liked': True,
        'data': {
            'id': like.id,
            'created_at': like.created_at.isoformat()
        }
    }, status=201)
    
@require_http_methods(['GET'])
def post_likes_list(request, channel_slug, post_slug):
    
    post = get_object_or_404(
        Post,
        slug=post_slug,
        channel__slug=channel_slug
    )
    
    content_type = ContentType.objects.get_for_model(Post)
    
    likes = Like.objects.filter(
        content_type=content_type,
        object_id=post.id
    ).order_by('-created_at')
    
    user_ids = [like.user_id for like in likes]
    users_data = get_users_batch(user_ids)
    users_map = {u['id']: u for u in users_data}
    
    data = []
    for like in likes:
        user_data = users_map.get(like.user_id)
        data.append({
            'id': like.id,
            'user_id': like.user_id,
            'user': {
                'id': user_data['id'],
                'email': user_data.get('email', ''),
                'avatar_url': user_data.get('avatar_url')
            } if user_data else None,
            'created_at': like.created_at.isoformat()
        })
    
    return JsonResponse({
        'success': True,
        'post': {
            'id': post.id,
            'title': post.title,
            'slug': post.slug
        },
        'count': len(data),
        'data': data
    }, status=200)
    

@require_http_methods(['GET'])
def post_likes_count(request, channel_slug, post_slug):
    
    post = get_object_or_404(
        Post,
        slug=post_slug,
        channel__slug=channel_slug
    )
    
    content_type = ContentType.objects.get_for_model(Post)
    
    count = Like.objects.filter(
        content_type=content_type,
        object_id=post.id
    ).count()
    
    is_liked = False
    
    if request.user.is_authenticated:
        is_liked = Like.objects.filter(
            user_id=request.user.id,
            content_type=content_type,
            object_id=post.id
        ).exists()
    
    return JsonResponse({
        'success': True,
        'post': {
            'id': post.id,
            'title': post.title,
            'slug': post.slug
        },
        'likes_count': count,
        'is_liked': False
    }, status=200)
