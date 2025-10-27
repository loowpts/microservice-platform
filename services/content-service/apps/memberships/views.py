import json
import logging
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.views.decorators.http import require_http_methods


from apps.common.api import get_user, get_users_batch, verify_user_exists
from apps.common.proxies import UserProxy
from apps.content.models import Channel
from .models import ChannelMembership
from .forms import ChannelMembershipForm

logger = logging.getLogger(__name__)


@require_http_methods(['GET'])
def member_list(request, slug):
    channel = get_object_or_404(Channel, slug=slug)
    
    memberships = channel.memberships.all().order_by('-joined_at')
    
    user_ids = [ch.user_id for ch in memberships]
    users_data = get_users_batch(user_ids)
    users_map = {o['id']: o for o in users_data}
    
    data = []
    for membership in memberships:
        user_data = users_map.get(memberships.user_id)
        data.append({
            'user_id': memberships.user_id,
            'role': memberships.role,
            'joined_at': memberships.joined_at.isoformat(),
            'user': {
                'id': user_data['id'],
                'email': user_data.get('email', ''),
                'avatar': user_data.get('avatar')
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
        
