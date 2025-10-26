from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.views.decorators.http import require_http_methods
import json
import logging

from apps.common.proxies import UserProxy
from .models import Channel
from apps.posts.models import Post
from apps.interactions.models import Like
from .forms import ChannelForm, ChannelUpdateForm, ChannelSearchForm
from apps.memberships.models import ChannelMembership
from apps.common.api import get_user, get_users_batch, verify_user_exists

logger = logging.getLogger(__name__)


# @property
# def get_owner(self):
#     user_data = get_user(self.owner_id)
#     if user_data:
#         return UserProxy.from_api(user_data)
#     return None

@require_http_methods(['GET'])
def channel_list(request):
    channels = Channel.objects.all()
    
    owner_ids = [ch.owner_id for ch in channels]
    
    owners_data = get_users_batch(owner_ids)
    owners_map = {o['id']: o for o in owners_data}
    
    data = []
    for channel in channels:
        owner_data = owners_map.get(channel.owner_id)
        data.append({
            'id': channel.id,
            'name': channel.name,
            'slug': channel.slug,
            'owner_id': channel.owner_id,
            'owner': {
                'id': owner_data['id'],
                'username': owner_data.get('username', ''),
            } if owner_data else None,
        })
        
    return JsonResponse({
        'success': True,
        'data': len(data),
        'data': data,
    }, status=200)


@require_http_methods(["POST"])
def create_channel(request):
    if not verify_user_exists(request.user.id):
        return JsonResponse({
            'success': False,
            'error': 'User not found in User Service'
        }, status=404)
    
    form = ChannelForm(request.POST)
    
    if form.is_valid():
        channel = form.save(commit=False)
        channel.owner_id = request.user.id
        channel.save()
        
        owner_data = get_user(request.user.id)
        
        return JsonResponse({
            'success': True,
            'data': {
                'id': channel.id,
                'slug': channel.slug,
                'owner': {
                    'id': owner_data['id'],
                    'username': owner_data['username'],
                } if owner_data else None,
            }
        }, status=201)
    
    return JsonResponse({
        'success': False,
        'errors': form.errors
    }, status=400)


@require_http_methods(["PUT"])
def update_channel(request, slug):
    channel = get_object_or_404(Channel, slug=slug)
    
    if channel.owner_id != request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'У вас нет прав для редактирования этого канала',
            'code': 'permission_denied'
        }, status=403)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Невалидный JSON'
        }, status=400)
    
    form = ChannelUpdateForm(data, instance=channel)
    
    if form.is_valid():
        channel = form.save()
        logger.info(f'Channel updated: {channel.slug} by user {request.user.id}')
        
        return JsonResponse({
            'success': True,
            'message': 'Канал успешно обновлен',
            'data': {
                'id': channel.id,
                'name': channel.name,
                'slug': channel.slug,
                'description': channel.description,
                'updated_at': channel.updated_at.isoformat(),
            }
        }, status=200)
    
    return JsonResponse({
        'success': False,
        'error': 'Ошибка валидации',
        'errors': form.errors
    }, status=400)
    

@require_http_methods(['GET'])  
def channel_detail(request, slug):
    channel = get_object_or_404(Channel, slug=slug)
    
    owner_data = get_user(channel.owner_id)
    
    members_count = channel.memberships.count()
    posts_count = channel.posts.count()
    
    return JsonResponse({
        'success': True,
        'data': {
            'id': channel.id,
            'name': channel.name,
            'slug': channel.slug,
            'description': channel.description,
            'owner_id': channel.owner_id,
            'owner': {
                'id': owner_data['id'],
                'email': owner_data.get('email', ''),
                'avatar_url': owner_data.get('avatar_url'),
            } if owner_data else None,
            'members_count': members_count,
            'posts_count': posts_count,
            'created_at': channel.created_at.isoformat(),
            'updated_at': channel.updated_at.isoformat(),
        }
    }, status=200)


@require_http_methods(['DELETE'])
def delete_channel(request, slug):
    channel = get_object_or_404(Channel, slug=slug)
    
    if channel.owner_id != request.user.id:
        return JsonResponse({
            'success': False,
            'message': 'У вас нет прав для удаления этого канала.',
            'code': 'permission_denied'
        }, status=403)
    
    
    channel_name = channel.name
    channel.delete()
    logger.info(f'Channel: {channel_name} (slug: {slug}) deleted by user - {request.user.id}')
        
    return JsonResponse({
        'success': False,
        'message': 'Invalid method',
    }, status=200)


@require_http_methods(['GET'])
def search_channel(request):
    form = ChannelSearchForm(request.GET or None)
    
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'error': 'Параметр query обязателен.',
            'errors': form.errors
        }, status=400)
    
    query = form.cleaned_data.get('query')
    
    channels = Channel.objects.filter(
        Q(name__icontains=query) | Q(description__icontains=query)
    ).order_by('-created_at')[:50]
    
    owner_ids = [ch.owner_id for ch in channels]
    owners_data = get_users_batch(owner_ids)
    owners_map = {o['id']: o for o in owners_data}
    
    data = []
    for channel in channels:
        owner_data = owners_map.get(channel.owner_id)
        data.append({
            'id': channel.id,
            'name': channel.name,
            'slug': channel.slug,
            'description': channel.description[:200] + '...' if len(channel.description) > 200 else channel.description,
            'owner_id': channel.owner_id,
            'owner': {
                'id': owner_data['id'],
                'email': owner_data.get('email', ''),
            } if owner_data else None,
            'members_count': channel.memberships.count(),
            'posts_count': channel.posts.count(),
            'created_at': channel.created_at.isoformat(),
        }) 
          
    logger.info(f'Channel search: query="{query}", results={len(data)}')

    return JsonResponse({
        'success': True,
        'query': query,
        'count': len(data),
        'data': data
    }, status=200)
