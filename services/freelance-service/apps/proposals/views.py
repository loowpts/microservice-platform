import json
import logging
from django.utils import timezone
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from apps.common.api import get_user, get_users_batch
from .models import CustomProposal
from apps.gigs.models import Gig
from apps.orders.models import Order
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


@require_http_methods(['GET'])
def proposal_detail(request, proposal_id):
    proposal = get_object_or_404(
        CustomProposal.objects.select_related('gig'), id=proposal_id
        )
    
    if proposal.seller_id != request.user.id and proposal.buyer_id != request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'У вас нет доступа к этому предложению'
        }, status=403)
    
    proposal.mark_as_expired()
    
    buyer = get_user(proposal.buyer_id)
    seller = get_user(proposal.seller_id)
    
    response_data = {
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
            'seller_id': proposal.gig.seller_id,
        },
        'seller_id': proposal.seller_id,
        'buyer_id': proposal.buyer_id,
        'seller': seller,
        'buyer': buyer,
        'is_expired': proposal.is_expired(),
        'can_accept': proposal.can_accept(),
        'expires_at': proposal.expires_at.isoformat(),
        'created_at': proposal.created_at.isoformat(),
        'updated_at': proposal.updated_at.isoformat(),
        'accepted_at': proposal.accepted_at.isoformat() if proposal.accepted_at else None,
        'rejected_at': proposal.rejected_at.isoformat() if proposal.rejected_at else None,
    }
    
    logger.info(f'Proposal viewed: {proposal.id}')
    
    return JsonResponse({
        'success': True,
        'data': response_data
    })

@require_http_methods(['POST'])
def proposal_create(request):
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
        
    gig_id = data.get('gig_id')
    buyer_id = data.get('buyer_id')
    
    if not gig_id or not buyer_id:
        return JsonResponse({
            'success': False,
            'error': 'gig_id and buyer_id are required'
        }, status=400)
    
    gig = get_object_or_404(Gig, id=gig_id)
    
    if gig.seller_id != request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'Вы не можете создать предложение для чужой услуги'
        }, status=403)
    
    if buyer_id == request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'Вы не можете создать предложение самому себе'
        }, status=403)
    
    if CustomProposal.objects.filter(
        gig=gig, seller_id=request.user.id, buyer_id=buyer_id, status='pending'
        ).exists():
        return JsonResponse({
            'success': False,
            'error': 'У вас уже есть активное предложение для этого клиента'
        }, status=400)
    
    form = ProposalForm(data)
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)
    
    proposal = form.save(commit=False)
    proposal.gig = gig
    proposal.seller_id = request.user.id
    proposal.buyer_id = buyer_id
    proposal.save()

    buyer = get_user(proposal.buyer_id)
    seller = get_user(proposal.seller_id)
    
    response_data = {
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
            'seller_id': proposal.gig.seller_id,
        },
        'seller_id': proposal.seller_id,
        'buyer_id': proposal.buyer_id,
        'seller': seller,
        'buyer': buyer,
        'is_expired': proposal.is_expired(),
        'can_accept': proposal.can_accept(),
        'expires_at': proposal.expires_at.isoformat(),
        'created_at': proposal.created_at.isoformat(),
        'updated_at': proposal.updated_at.isoformat(),
    }
    
    logger.info(f'Proposal created: {proposal.id} from {request.user.id} to {buyer_id}')
    
    return JsonResponse({
        'success': True,
        'message': 'Предложение успешно создано',
        'data': response_data
    }, status=201)
    
@require_http_methods(['PATCH'])
def proposal_accept(request, proposal_id):
    proposal = get_object_or_404(CustomProposal, id=proposal_id)
    
    if proposal.buyer_id != request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'Только получатель может принять предложение'
        }, status=403)
    
    proposal.mark_as_expired()
    
    if not proposal.can_accept():
        if proposal.is_expired():
            return JsonResponse(
                {
                    'success': False,
                    'error': 'Предложение истекло',
                    'code': 'proposal_expired'
                },
                status=400
            )
        else:  # Статус не pending
            return JsonResponse(
                {
                    'success': False,
                    'error': 'Предложение уже обработано',
                    'code': 'proposal_already_processed'
                },
                status=400
            )
    
    order = Order.objects.create(
        gig=proposal.gig,
        seller_id=proposal.seller_id,
        buyer_id=proposal.buyer_id,
        package_type='custom',
        title=proposal.title,
        description=proposal.description,
        price=proposal.price,
        delivery_days=proposal.delivery_days,
        revisions=proposal.revisions,
        status='pending'
    )
    
    proposal.status = 'accepted'
    proposal.accepted_at = timezone.now()
    proposal.save(update_fields=['status', 'accepted_at'])
    
    seller = get_user(proposal.seller_id)
    buyer = get_user(proposal.buyer_id)
    
    response_data = {
        'order': {
            'id': order.id,
            'gig_id': order.gig_id,
            'seller': seller,
            'buyer': buyer,
            'package_type': order.package_type,
            'title': order.title,
            'description': order.description,
            'price': float(order.price),
            'delivery_days': order.delivery_days,
            'revisions': order.revisions,
            'status': order.status,
            'created_at': order.created_at.isoformat()
        },
        'proposal': {
            'id': proposal.id,
            'status': proposal.status,
            'accepted_at': proposal.accepted_at.isoformat()
        }
    }
    
    logger.info(f'Proposal accepted: {proposal.id}, Order created: {order.id}')
    
    return JsonResponse({
        'success': True,
        'message': 'Предложение принято, заказ создан',
        'order_id': order.id,
        'data': response_data
    }, status=200)
    
@require_http_methods(['PATCH'])
def proposal_reject(request, proposal_id):
    proposal = get_object_or_404(CustomProposal, id=proposal_id)
    
    if proposal.buyer_id != request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'Только получатель может отклонить предложение'
        }, status=403)
    
    if proposal.status != 'pending':
        return JsonResponse({
            'success': False,
            'error': 'Можно отклонить только активное предложение'
        }, status=400)
    
    proposal.status = 'rejected'
    proposal.rejected_at = timezone.now()
    proposal.save(update_fields=['status', 'rejected_at'])
    
    seller = get_user(proposal.seller_id)
    buyer = get_user(proposal.buyer_id)
    
    response_data = {
        'id': proposal.id,
        'gig_id': proposal.gig_id,
        'seller_id': proposal.seller_id,
        'buyer_id': proposal.buyer_id,
        'seller': seller,
        'buyer': buyer,
        'title': proposal.title,
        'description': proposal.description,
        'price': float(proposal.price),
        'delivery_days': proposal.delivery_days,
        'revisions': proposal.revisions,
        'status': proposal.status,
        'rejected_at': proposal.rejected_at.isoformat(),
        'created_at': proposal.created_at.isoformat(),
        'updated_at': proposal.updated_at.isoformat(),
    }
    
    logger.info(f'Proposal rejected: {proposal.id}')
    
    return JsonResponse({
        'success': True,
        'message': 'Предложение отклонено',
        'data': response_data
    }, status=200)
    
