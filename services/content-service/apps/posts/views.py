import json
import logging
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from apps.common.api import get_user, get_users_batch
from apps.content.models import Channel, ChannelRole
from apps.memberships.models import ChannelMembership
from .models import Post
from .forms import PostForm, PostSearchForm
from apps.interactions.models import View

logger = logging.getLogger(__name__)


@require_http_methods(['GET'])
def post_list(request, channel_slug):
    channel = get_object_or_404(Channel, slug=channel_slug)
    
    posts = channel.posts.all()
    
    author_ids = [post.author_id for post in posts]
    authors_data = get_users_batch(author_ids)
    authors_map = {o['id']: o for o in authors_data}
    
    data = []
    for post in posts:
        author_data = authors_map.get(post.author_id)
        data.append({
            'id': post.id,
            'title': post.title,
            'slug': post.slug,
            'content': post.content[:200] + '...' if len(post.content) > 200 else post.content,
            'author_id': post.author_id,
            'author': {
                'id': author_data['id'],
                'email': author_data.get('email', ''),
                'avatar_url': author_data.get('avatar_url')
            } if author_data else None,
            'image_url': post.image_url,
            'comments_count': post.comments.count(),
            'created_at': post.created_at.isoformat(),
        })
        
    logger.info(f'Post list requested for channel: {channel_slug}, count: {len(data)}')
    
    return JsonResponse({
        'success': True,
        'channel': {
            'id': channel.id,
            'name': channel.name,
            'slug': channel.slug
        },
        'count': len(data),
        'data': data
    }, status=200)
    

@require_http_methods(['POST'])
def post_create(request, channel_slug):
    channel = get_object_or_404(Channel, slug=channel_slug)
    
    membership = ChannelMembership.objects.filter(
        channel=channel,
        user_id=request.user.id
    )
    
    if not membership:
        return JsonResponse({
            'success': False,
            'error': 'Вы не являетесь членом этого канала',
            'code': 'not_a_member'
        }, status=403)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Невалидный Json'
        }, status=400)
    
    form = PostForm(data)
    
    if form.is_valid():
        post = form.save(commit=False)
        post.channel = channel
        post.author_id = request.user.id
        post.save()
        
        author_data = get_user(request.user.id)
        
        logger.info(f'Post created: {post.title} in {channel_slug} by user {request.user.id}')
        
        return JsonResponse({
            'success': True,
            'message': 'Пост успешно создан.',
            'data': {
                'id': post.id,
                'title': post.title,
                'slug': post.slug,
                'content': post.content,
                'channel': {
                    'id': channel.id,
                    'name': channel.name,
                    'slug': channel.slug
                },
                'author': {
                    'id': author_data['id'],
                    'email': author_data.get('email', ''),
                } if author_data else None,
                'created_at': post.created_at.isoformat(),
            }
        }, status=201)
    
    return JsonResponse({
        'success': False,
        'error': 'Ошибка валидации'
        'errors': form.errors
    }, status=400)
    

@require_http_methods(['GET'])
def post_detail(request, channel_slug, post_slug):
    post = get_object_or_404(
        Post,
        slug=post_slug,
        channel__slug=channel_slug
    )
    
    View.objects.create(
        post=post,
        user_id=request.user.id if request.user.is_authenticated else None,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.MET.get('HTTP_USER_AGENT', '')[:512]
    )
    
    author_data = get_user(post.author_id)
    
    views_count = post.views.count()
    comments_count = post.comments.count()
    
    return JsonResponse({
        'success': True,
        'data': {
            'id': post.id,
            'title': post.title,
            'slug': post.slug,
            'content': post.content,
            'author_id': post.author_id,
            'author': {
                'id': author_data['id'],
                'email': author_data.get('email', ''),
                'avatar_url': author_data.get('avatar_url'),          
            } if author_data else None,
            'image_url': post.image_url,
            'channel': {
                'id': post.channel.id,
                'slug': post.channel.slug,
                'name': post.channel.name
            },
            'views_count': views_count,
            'comments_count': comments_count,
            'created_at': post.created_at.isoformat(),
            'updated_at': post.updated_at.isoformat(),
        }
    }, status=200)
    

@require_http_methods(['PATCH'])
def post_update(request, channel_slug, post_slug):
    post = get_object_or_404(
        Post,
        post_slug=post_slug,
        channel__slug=channel_slug
    )
    
    membership = post.channel.memberships.filter(
        user_id=request.user.id
    ).first()
    
    if not post.can_edit(request.user.id, membership.role if membership else None)
        return JsonResponse({
            'success': False,
            'error': 'У вас нет прав для редактирования этого поста.',
            'code': 'permission_denied'
        }, status=403)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Невалидный Json'
        }, status=400)
    
    form = PostForm(data, instance=post)
    if form.is_valid():
        form.save()
        
        logger.info(f'Post updated: {post.slug} by user - {request.user.id}')
        
        return JsonResponse({
            'success': True,
            'message': 'Пост успешно обновлён.',
            'data': {
                'id': post.id,
                'title': post.title,
                'slug': post.slug,
                'content': post.content,
                'updated_at': post.updated_at.isoformat(),
            }
        }, status=200)
        
    return JsonResponse({
        'success': False,
        'error': form.errors
    }, status=404)


@require_http_methods(['DELETE'])
def post_delete(request, channel_slug, post_slug):
    post = get_object_or_404(
        Post,
        slug=post_slug,
        channel__slug=channel_slug
    )
    membership = post.channel.memberships.filter(
        user_id=request.user.id
    ).first()
    
    if not post.can_edit(request.user.id, membership.role if membership else None):
        return JsonResponse({
            'success': False,
            'error': 'У вас нет прав для удаления этого поста.',
            'code': 'permission_denied'
        }, status=403)
    
        
    post_title = post.title
    post_id = post.id
    post_slug_saved = post.slug
    channel_data = {
        'id': post.channel.id,
        'name': post.channel.name,
        'slug': post.channel.slug,
    }
    
    post.delete()
    
    logger.info(f'Post deleted: {post_title} (slug: {post_slug_saved}) by user {request.user.id}')
    
    return JsonResponse({
        'success': True,
        'message': f'Пост "{post_title}" успешно удалён',
        'data': {
            'id': post_id,
            'title': post_title,
            'slug': post_slug_saved,
            'channel': channel_data
        }
    }, status=200)
        
    
