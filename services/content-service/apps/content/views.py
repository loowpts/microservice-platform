from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
import json
import logging

from apps.common.proxies import UserProxy
from apps.common.api import get_user
from .models import Channel, Post, Like
from .forms import ChannelForm, ChannelUpdateForm

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
    
    data = [{
        'id': ch.id,
        'name': ch.name,
        'slug': ch.slug,
        'description': ch.description,
        'owner_id': ch.owner_id,
        'created_at': ch.created_at.isoformat()
    } for ch in channels]
    
    return JsonResponse({
        'success': True,
        'data': len(data),
        'data': data,
    }, status=200)

@require_http_methods(["POST"])
def create_channel(request):
    form = ChannelForm(request.POST)
    
    if form.is_valid():
        channel = form.save(commit=False)
        channel.owner_id = request.user.id
        channel.save()
        
        logger.info(f'Channel created: {channel.name}')
        
        return JsonResponse({
            'success': True,
            'message': 'Канал успешно создан',
            'data': {
                'id': channel.id,
                'name': channel.name,
                'slug': channel.slug,
                'description': channel.description,
                'owner_id': channel.owner_id,
                'created_at': channel.created_at.isoformat(),
            }
        }, status=201)
    
    logger.error(f"Form errors: {form.errors.as_json()}")
    
    return JsonResponse({
        'success': False,
        'error': 'Ошибка валидации',
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
    
            
