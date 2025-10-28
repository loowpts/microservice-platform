import json
import logging
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from apps.common.api import get_user, get_users_batch
from apps.content.models import Channel, ChannelRole
from .models import ChannelMembership

logger = logging.getLogger(__name__)


@require_http_methods(['GET'])
def member_list(request, slug):
    channel = get_object_or_404(Channel, slug=slug)
    
    membership = channel.memberships.all().order_by('-joined_at')
    
    user_ids = [ch.user_id for ch in membership]
    users_data = get_users_batch(user_ids)
    users_map = {o['id']: o for o in users_data}
    
    data = []
    for membership in membership:
        user_data = users_map.get(membership.user_id)
        data.append({
            'user_id': membership.user_id,
            'role': membership.role,
            'joined_at': membership.joined_at.isoformat(),
            'user': {
                'id': user_data['id'],
                'email': user_data.get('email', ''),
                'avatar_url': user_data.get('avatar_url')
            } if user_data else None
        })
        
    logger.info(f'Member list requested for channel: {slug}, count: {len(data)}')
    
    return JsonResponse({
        'success': True,
        'channel': {
            'id': channel.id,
            'name': channel.name,
            'slug': channel.slug,
        },
        'count': len(data),
        'data': data
    }, status=200)    
        

@require_http_methods(['POST'])
def member_join(request, slug):
    channel = get_object_or_404(Channel, slug=slug)
    
    if ChannelMembership.objects.filter(
        channel=channel,
        user_id=request.user.id
    ).exists():
        return JsonResponse({
            'success': False,
            'error': 'Вы уже являетесь членом этого канала',
            'code': 'already_member',
        }, status=409)
        
    membership = ChannelMembership.objects.create(
        channel=channel,
        user_id=request.user.id,
        role=ChannelRole.MEMBER
    )
    
    user_data=get_user(request.user.id)
    
    logger.info(f'{request.user.id} joined channel {channel.name} (slug: {slug})')
    
    return JsonResponse({
        'success': True,
        'message': f'Вы успешно вступили в канал: {channel.name}',
        'data': {
            'user_id': membership.user_id,
            'role': membership.role,
            'joined_at': membership.joined_at.isoformat(),
            'channel': {
                'id': channel.id,
                'name': channel.name,
                'slug': channel.slug,
            },
            'user': {
                'id': user_data['id'],
                'email': user_data.get('email'),
                'avatar_url': user_data.get('avatar_url')
            } if user_data else None,
        }
    }, status=201)
    
    

@require_http_methods(['DELETE'])
def member_leave(request, slug):
    channel = get_object_or_404(Channel, slug=slug)
    
    if channel.owner_id == request.user.id:
        return JsonResponse({
            'success': False,
            'message': 'Владелец не может покинуть свой канал.',
            'code': 'owner_cannot_leave',
        }, status=403)
        
    try:
        memberships = ChannelMembership.objects.get(
            channel=channel,
            user_id=request.user.id
        )
    except ChannelMembership.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Вы не являетесь членом этого канала.',
            'code': 'note_a_member',
        }, status=404)
        
    memberships.delete()
    
    logger.info(f'{request.user.id} left channel {channel.name} (slug: {slug})')
    
    return JsonResponse({
        'success': True,
        'message': f'Вы успешно покинули канал: {channel.name}'
    }, status=200)


@require_http_methods(['PATCH'])
def member_update_role(request, slug, user_id):
    channel = get_object_or_404(Channel, slug=slug)
    
    if channel.owner_id != request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'Вы не являетесь владельцем канала.',
            'code': 'permission_denied'
        }, status=403)
        
    if int(user_id) == request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'Вы не можете поменять себе роль',
            'code': 'cannot_change_own_role'
        }, status=403)
        
    try:
        membership = ChannelMembership.objects.get(
            channel=channel,
            user_id=int(user_id)
        )
    except ChannelMembership.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Пользователь не является членом этого канала.',
            'code': 'member_not_found'
        }, status=404)
        
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Невалидный Json'
        }, status=400)
    
    new_role = data.get('role', '').strip()
    
    if not new_role:
        return JsonResponse({
            'success': False,
            'error': 'Параметр role обязателен.'
        }, status=400)
        
    valid_roles = [choice[0] for choice in ChannelRole.choices]
    if new_role not in valid_roles:
        return JsonResponse({
            'success': False,
            'error': f'Невалидная роль. Допустимые: {", ".join(valid_roles)}'
        }, status=400)
        
    if new_role == ChannelRole.OWNER:
        return JsonResponse({
            'success': False,
            'error': 'Нельзя назначить роль owner другому пользователю',
            'code': 'cannot_assign_owner'
        }, status=403)
        
    old_role = membership.role
    
    membership.role = new_role
    membership.save()
    
    user_data = get_user(membership.user_id)
    
    logger.info(
        f'User: {request.user.id} changed role of user {user_id} '
        f'from {old_role} to {new_role} in channel {slug}'
    )
    
    return JsonResponse({
        'success': True,
        'message': f'Роль успешна изменена с {old_role} на ({new_role})',
        'data': {
            'user_id': membership.user_id,
            'role': membership.role,
            'previous_role': old_role,
            'joined_at': membership.joined_at.isoformat(),
            'channel': {
                'id': channel.id,
                'name': channel.name,
                'slug': channel.slug
            },
            'user': {
                'id': user_data['id'],
                'email': user_data.get('email', ''),
                'avatar_url': user_data.get('avatar_url')
            } if user_data else None
        }
    }, status=200)
    

@require_http_methods(['DELETE'])
def member_remove(request, slug, user_id):
    channel = get_object_or_404(Channel, slug=slug)
    
    current_user_membership = ChannelMembership.objects.filter(
        channel=channel,
        user_id=request.user.id
    ).first()
    
    if not current_user_membership:
        return JsonResponse({
            'success': False,
            'error': 'Вы не являетесь членом этого канала',
            'code': 'not_a_member'
        }, status=403)
    
    if current_user_membership.role not in [ChannelRole.OWNER, ChannelRole.ADMIN]:
        return JsonResponse({
            'success': False,
            'error': 'У вас нету прав для удаления участников.',
            'code': 'permission_denied'
        }, status=403)
    
    if int(user_id) == request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'Вы не можете удалить самого себя. Используйте /leave/',
            'code': 'cannot_remove_self'
        }, status=403)
        
    try:
        membership = ChannelMembership.objects.get(
            channel=channel,
            user_id=int(user_id)
        )
    except ChannelMembership.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Пользователь не является членом этого канала.',
            'code': 'member_not_found'
        }, status=404)
        
    if membership.role == ChannelRole.OWNER:
        return JsonResponse({
            'success': False,
            'error': 'Нельзя удалить владельца канала.',
            'code': 'cannot_remove_owner'
        }, status=403)
        
    
    if membership.role == ChannelRole.ADMIN and current_user_membership.role != ChannelRole.OWNER:
        return JsonResponse({
            'success': False,
            'error': 'Только владелец канала может удалять администраторов',
            'code': 'cannot_remove_admin'
        }, status=403)
    
    removed_user_id = membership.user_id
    removed_role = membership.role
    joined_at = membership.joined_at
    
    user_data = get_user(membership.user_id)
    membership.delete()
    
    logger.info(
        f'User ({request.user.id}) removed user {removed_user_id}'
        f'(role {removed_role}) from channel {slug}'
        )
    
    return JsonResponse({
        'success': True,
        'message': 'Пользователь успешно удален из канала',
        'data': {
            'user_id': removed_user_id,
            'role': removed_role,
            'joined_at': joined_at.isoformat(),
            'channel': {
                'id': channel.id,
                'name': channel.name,
                'slug': channel.slug,
            },
            'user': {
                'id': user_data['id'],
                'username': user_data.get('username', ''),
                'email': user_data.get('email', ''),
                'avatar_url': user_data.get('avatar_url'),
            } if user_data else None,
        }
    }, status=200)
