import json
import logging
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from apps.common.api import get_user, get_users_batch
from .models import CustomProposal, PROPOSAL_STATUS_CHOICES
from .forms import ProposalForm

logger = logging.getLogger(__name__)


@require_http_methods(['GET'])
def proposal_list(request):
    
    type_param = request.GET.get('type', 'received')
    status = request.GET.get('status')
    
    proposals = CustomProposal.objects.all()
    
    if type_param == 'sent':
        proposals = proposals.filter(seller_id=request.user.id)
    elif type_param == 'received':
        proposals = proposals.filter(buyer_id=request.user.id)
    
    if status:
        proposals = proposals.filter(status=status)
    
    proposals = proposals.order_by('-created_at').select_related('gig')

    for proposal in proposals:
        if proposal.status == 'pending':
            proposal.mark_as_expired()
    
    if type_param == 'sent':
        user_ids = [p.buyer_id for p in proposals]
    else:
        user_ids = [p.seller_id for p in proposals]
    
    users_data = get_users_batch(user_ids)
    users_map = {u['id']: u for u in users_data}
    
    data = []
    for proposal in proposals:
        if type_param == 'sent':
            user = users_map.get(proposal.buyer_id)
            user_id = proposal.buyer_id
        else:
            user = users_map.get(proposal.seller_id)
            user_id = proposal.seller_id
        
        proposal_data = {
            'id': proposal.id,
            'title': proposal.title,
            'description': proposal.description,
            'price': float(proposal.price),
            'delivery_days': proposal.delivery_days,
            'revisions': proposal.revisions,
            'status': proposal.status,
            'buyer_message': proposal.buyer_message if proposal.buyer_message else '',
            'gig': {
                'id': proposal.gig.id,
                'title': proposal.gig.title,
                'slug': proposal.gig.slug,
            },
            'is_expired': proposal.is_expired(),
            'can_accept': proposal.can_accept(),
            'expires_at': proposal.expires_at.isoformat(),
            'created_at': proposal.created_at.isoformat(),
            'updated_at': proposal.updated_at.isoformat(),
            'accepted_at': proposal.accepted_at.isoformat() if proposal.accepted_at else None,
            'rejected_at': proposal.rejected_at.isoformat() if proposal.rejected_at else None,
        }
        
        if type_param == 'sent':
            proposal_data['buyer_id'] = user_id
            proposal_data['buyer'] = user
        else:
            proposal_data['seller_id'] = user_id
            proposal_data['seller'] = user
        
        data.append(proposal_data)
    
    return JsonResponse({
        'success': True,
        'count': len(data),
        'data': data
    })
