import json
import logging
from django.utils import timezone
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.db.models import Q

from apps.gigs.models import Gig, GigPackage
from apps.common.api import get_user, get_users_batch
from apps.orders.models import Order
from .models import Order, OrderRequirement, Dispute, DisputeMessage
from .forms import OrderCreateForm, OrderDeliveryForm
from apps.common.notifications import send_notification

logger = logging.getLogger(__name__)

@require_http_methods(['GET'])
def order_list(request):
    role = request.GET.get('role', 'buyer')
    status = request.GET.get('status')
    
    orders = Order.objects.all()
    
    if role == 'buyer':
        orders = orders.filter(buyer_id=request.user.id)
    elif role == 'seller':
        orders = orders.filter(seller_id=request.user.id)
        
    if status:
        orders = orders.filter(status=status)
    
    orders = orders.order_by('-created_at').select_related('gig', 'package')
    
    if role == 'buyer':
        user_ids = [o.seller_id for o in orders]
    else:
        user_ids = [o.buyer_id for o in orders]
    
    user_data = get_users_batch(user_ids)
    users_map = {u['id']: u for u in user_data}
    
    data = []
    for order in orders:
        if role == 'buyer':
            user = users_map.get(order.seller_id)
            user_id = order.seller_id
            user_key = 'seller'
        else:
            user = users_map.get(order.buyer_id)
            user_id = order.buyer_id
            user_key = 'buyer'
        
        #Просрочен ли заказ
        is_overdue = order.is_overdue()
        
        order_data = {
            'id': order.id,
            'status': order.status,
            'gig': {
                'id': order.gig.id,
                'title': order.gig.title,
                'slug': order.gig.slug,
            },
            'package': {
                'type': order.package.type,
                'name': order.package.name,
                'price': float(order.package.price),
                'delivery_time': order.package.delivery_time,
            },
            'buyer_id': order.buyer_id,
            'seller_id': order.seller_id,
            'price': float(order.price),
            'delivery_time': order.delivery_time,
            'requirements': order.requirements if order.requirements else None,
            'deadline': order.deadline.isoformat(),
            'delivered_at': order.delivered_at.isoformat() if order.delivered_at else None,
            'completed_at': order.completed_at.isoformat() if order.completed_at else None,
            'is_overdue': is_overdue,
            'created_at': order.created_at.isoformat(),
            'updated_at': order.updated_at.isoformat(),
        }
        
        if role == 'buyer':
            order_data['seller'] = user
        else:
            order_data['buyer'] = user
            
        data.append(order_data)
    
    return JsonResponse({
        'success': True,
        'role': role,
        'count': len(data),
        'data': data
    })

@require_http_methods(['GET'])
def order_detail(request, order_id):
    order = get_object_or_404(Order.objects.select_related('gig', 'package'), id=order_id)
    
    if order.buyer_id != request.user.id and order.seller_id != request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'У вас нет доступа к этому заказу'
        }, status=403)
    
    buyer = get_user(order.buyer_id)
    seller = get_user(order.seller_id)
    
    requirements_files = order.requirement_files.all()
    requirements_files_data = [
        {
            'id': rf.id,
            'file_url': rf.file_url,
            'description': rf.description,
            'created_at': rf.created_at.isoformat()
        }
        for rf in requirements_files
    ]
    deliveries = order.deliveries.all()
    deliveries_data = [
        {
            'id': d.id,
            'message': d.message,
            'file_url': d.file_url,
            'created_at': d.created_at.isoformat()
        }
        for d in deliveries
    ]
    
    is_overdue = order.is_overdue()
    
    response_data = {
        'id': order.id,
        'status': order.status,
        'gig': {
            'id': order.gig.id,
            'title': order.gig.title,
            'slug': order.gig.slug,
            'seller_id': order.seller_id,
        },
        'package': {
            'type': order.package.type,
            'name': order.package.name,
            'price': float(order.package.price),
            'delivery_time': order.package.delivery_time,
        },
        'buyer_id': order.buyer_id,
        'seller_id': order.seller_id,
        'buyer': buyer,
        'seller': seller,
        'price': float(order.price),
        'delivery_time': order.delivery_time,
        'requirements_files': requirements_files_data,
        'deliveries': deliveries_data,
        'requirements': order.requirements if order.requirements else None,
        'deadline': order.deadline.isoformat(),
        'delivered_at': order.delivered_at.isoformat() if order.delivered_at else None,
        'completed_at': order.completed_at.isoformat() if order.completed_at else None,
        'is_overdue': is_overdue,
        'can_be_cancelled': order.can_be_cancelled(),
        'can_be_delivered': order.can_be_delivered(),
        'can_be_completed': order.can_be_completed(),
        'created_at': order.created_at.isoformat(),
        'updated_at': order.updated_at.isoformat(),
    }
    
    logger.info(f'Viewed Order: user ({request.user.id})')
    
    return JsonResponse({
        'success': True,
        'data': response_data
    })

@require_http_methods(['POST'])
def order_create(request):
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    
    gig_id = data.get('gig_id')
    gig = get_object_or_404(Gig, id=gig_id, status='active')
    package_type = data.get('package_type')
    package = get_object_or_404(GigPackage, gig=gig, type=package_type)
    
    if not gig_id or not package_type:
        return JsonResponse({
            'success': False,
            'error': 'gig_id and package_type are required'
        }, status=400)
        
    if gig.seller_id == request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'Вы не можете купить свою услугу.'
        }, status=400)
    
    form = OrderCreateForm(data)
    
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)
        
    order = form.save(commit=False)
    order.gig = gig
    order.package = package
    order.buyer_id = request.user.id
    order.seller_id = gig.seller_id
    order.price = package.price
    order.delivery_time = package.delivery_time
    order.status = 'pending'
    order.save()
    
    send_notification(
        user_id=order.seller_id,
        event='order_created',
        title='Новый заказ!',
        message=f'У вас новый заказ #{order.id} на "{order.gig.title}" на сумму {order.price}₽',
        notification_type='in_app',
        data={
            'order_id': order.id,
            'gig_id': order.gig.id,
            'buyer_id': order.buyer_id
        }
    )
    
    requirement_files = data.get('requirement_files', [])
    for req_file in requirement_files:
        file_url = req_file.get('file_url')
        description = req_file.get('description', '')
        
        if file_url:
            OrderRequirement.objects.create(
                order=order,
                file_url=file_url,
                description=description
            )
    
    requirements_files = order.requirement_files.all()
    requirements_files_data = [
        {
            'id': rf.id,
            'file_url': rf.file_url,
            'description': rf.description,
            'created_at': rf.created_at.isoformat()
        }
        for rf in requirements_files
    ]
    
    buyer = get_user(order.buyer_id)
    seller = get_user(order.seller_id)
    
    response_data = {
        'id': order.id,
        'status': order.status,
        'gig': {
            'id': order.gig.id,
            'title': order.gig.title,
            'slug': order.gig.slug,
        },
        'package': {
            'type': order.package.type,
            'name': order.package.name,
            'price': float(order.package.price),
            'delivery_time': order.package.delivery_time,
        },
        'buyer_id': order.buyer_id,
        'seller_id': order.seller_id,
        'buyer': buyer,
        'seller': seller,
        'price': float(order.price),
        'delivery_time': order.delivery_time,
        'requirements': order.requirements,
        'requirement_files': requirements_files_data,
        'deadline': order.deadline.isoformat(),
        'is_overdue': order.is_overdue(),
        'can_be_cancelled': order.can_be_cancelled(),
        'created_at': order.created_at.isoformat(),
        'updated_at': order.updated_at.isoformat(),
    }

    logger.info(f'Order created: {order.id} by buyer {request.user.id}')
    
    return JsonResponse({
        'success': True,
        'message': 'Заказ успешно создан',
        'data': response_data
    }, status=201)
    

@require_http_methods(['PATCH'])
def order_update_status(request, order_id):
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    
    order = get_object_or_404(Order, id=order_id)
    new_status = data.get('status')
    
    if not new_status:
        return JsonResponse({
            'success': False,
            'error': 'status is required'
        }, status=400)
        
    if new_status == 'in_progress':
        if order.seller_id != request.user.id:
            return JsonResponse({
                'success': False,
                'error': 'Только продавец может принять заказ'
            }, status=403)
        
        if order.status != 'pending':
            return JsonResponse({
                'success': False,
                'error': 'Можно принять только заказ в статусе "ожидает подтверждения"',
                'code': 'invalid_status_transition'
            }, status=400)
    else:
        return JsonResponse({
            'success': False,
            'error': 'Недопустимое изменение статуса',
            'code': 'invalid_status'
        }, status=400)
        
    order.status = new_status
    order.save(update_fields=['status', 'updated_at'])
    
    buyer = get_user(order.buyer_id)
    seller = get_user(order.seller_id)
    
    response_data = {
        'id': order.id,
        'status': order.status,
        'gig': {
            'id': order.gig.id,
            'title': order.gig.title,
            'slug': order.gig.slug,
        },
        'package': {
            'type': order.package.type,
            'name': order.package.name,
            'price': float(order.package.price),
            'delivery_time': order.package.delivery_time,
        },
        'buyer_id': order.buyer_id,
        'seller_id': order.seller_id,
        'buyer': buyer,
        'seller': seller,
        'price': float(order.price),
        'delivery_time': order.delivery_time,
        'requirements': order.requirements,
        'deadline': order.deadline.isoformat(),
        'delivered_at': order.delivered_at.isoformat() if order.delivered_at else None,
        'completed_at': order.completed_at.isoformat() if order.completed_at else None,
        'is_overdue': order.is_overdue(),
        'can_be_cancelled': order.can_be_cancelled(),
        'can_be_delivered': order.can_be_delivered(),
        'can_be_completed': order.can_be_completed(),
        'created_at': order.created_at.isoformat(),
        'updated_at': order.updated_at.isoformat(),
    }
    
    logger.info(f'Order status updated: {order.id} from pending to {new_status} by user {request.user.id}')
    
    return JsonResponse({
        'success': True,
        'message': 'Статус заказа обновлён',
        'data': response_data
    }, status=200)
    
@require_http_methods(['POST'])
def order_deliver(request, order_id):
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    
    order = get_object_or_404(Order, id=order_id)
    
    if order.seller_id != request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'Только продавец может отправить результат работы'
        }, status=403)
    
    if not order.can_be_delivered():
        return JsonResponse({
            'success': False,
            'error': 'Отправить результат можно только для заказа в статусе "в работе"'
        }, status=400)
    
    form = OrderDeliveryForm(data)
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)
    
    delivery = form.save(commit=False)
    delivery.order = order
    delivery.save()
    
    send_notification(
        user_id=order.buyer_id,
        event='order_delivered',
        title='Результат работы получен',
        message=f'Продавец отправил результат по заказу #{order.id}. Проверьте работу.',
        notification_type='in_app',
        data={
            'order_id': order.id,
            'delivery_id': delivery.id
        }
    )
    
    order.status = 'delivered'
    order.delivered_at = timezone.now()
    order.save(update_fields=['status', 'delivered_at', 'updated_at'])
    
    buyer = get_user(order.buyer_id)
    seller = get_user(order.seller_id)
    
    response_data = {
        'delivery': {
            'id': delivery.id,
            'message': delivery.message,
            'file_url': delivery.file_url,
            'created_at': delivery.created_at.isoformat()
        },
        'order': {
            'id': order.id,
            'status': order.status,
            'gig': {
                'id': order.gig.id,
                'title': order.gig.title,
                'slug': order.gig.slug,
            },
            'package': {
                'type': order.package.type,
                'name': order.package.name,
                'price': float(order.package.price),
                'delivery_time': order.package.delivery_time,
            },
            'buyer_id': order.buyer_id,
            'seller_id': order.seller_id,
            'buyer': buyer,
            'seller': seller,
            'price': float(order.price),
            'delivery_time': order.delivery_time,
            'requirements': order.requirements,
            'deadline': order.deadline.isoformat(),
            'delivered_at': order.delivered_at.isoformat(),
            'completed_at': order.completed_at.isoformat() if order.completed_at else None,
            'is_overdue': order.is_overdue(),
            'can_be_cancelled': order.can_be_cancelled(),
            'can_be_delivered': order.can_be_delivered(),
            'can_be_completed': order.can_be_completed(),
            'created_at': order.created_at.isoformat(),
            'updated_at': order.updated_at.isoformat(),
        }
    }
    
    logger.info(f'Order delivered: {order.id}')
    
    return JsonResponse({
        'success': True,
        'message': 'Результат работы отправлен',
        'data': response_data
    }, status=201)

@require_http_methods(['POST'])
def order_complete(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if order.buyer_id != request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'У вас нет прав для выполнения этой задачи.'
        }, status=403)
    
    if not order.can_be_completed():
        return JsonResponse({
            'success': False,
            'error': 'Отправить результат можно только для заказа в статусе "в работе"',
        }, status=400)
    
    order.status = 'completed'
    order.completed_at = timezone.now()
    order.save(update_fields=['status', 'completed_at', 'updated_at'])
    
    order.gig.orders_count += 1
    order.gig.save(update_fields=['orders_count'])
    
    send_notification(
        user_id=order.seller_id,
        event='order_completed',
        title='Заказ завершён',
        message=f'Заказ #{order.id} успешно завершён покупателем. Средства зачислены.',
        notification_type='in_app',
        data={
            'order_id': order.id,
            'amount': float(order.price)
        }
    )   
    buyer = get_user(order.buyer_id)
    seller = get_user(order.seller_id)
    
    response_data = {
        'id': order.id,
        'status': order.status,
        'gig': {
            'id': order.gig.id,
            'title': order.gig.title,
            'slug': order.gig.slug,
        },
        'package': {
            'type': order.package.type,
            'name': order.package.name,
            'price': float(order.package.price),
            'delivery_time': order.package.delivery_time,
        },
        'buyer_id': order.buyer_id,
        'seller_id': order.seller_id,
        'buyer': buyer,
        'seller': seller,
        'price': float(order.price),
        'delivery_time': order.delivery_time,
        'requirements': order.requirements,
        'deadline': order.deadline.isoformat(),
        'delivered_at': order.delivered_at.isoformat() if order.delivered_at else None,
        'completed_at': order.completed_at.isoformat() if order.completed_at else None,
        'is_overdue': order.is_overdue(),
        'can_be_cancelled': order.can_be_cancelled(),
        'can_be_delivered': order.can_be_delivered(),
        'can_be_completed': order.can_be_completed(),
        'created_at': order.created_at.isoformat(),
        'updated_at': order.updated_at.isoformat(),
    }

    logger.info(f'Order completed: {order.id}')
    
    return JsonResponse({
        'success': True,
        'message': 'Заказ успешно завершен',
        'data': response_data
    }, status=200)

@require_http_methods(['POST'])
def order_cancel(request, order_id):
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    
    order = get_object_or_404(Order, id=order_id)
    
    cancellation_reason = data.get('reason', '')
    
    if order.buyer_id != request.user.id and order.seller_id != request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'Вы не можете отменить чужой заказ.'
        }, status=403)
    
    if not order.can_be_cancelled():
        return JsonResponse({
            'success': False,
            'error': 'Отменить можно только заказы в статусе "ожидает подтверждения" или "в работе"'
        }, status=400)
        
    order.status = 'cancelled'
    order.save(update_fields=['status', 'updated_at'])
    
    recipient_id = order.seller_id if order.buyer_id == request.user.id else order.buyer_id

    send_notification(
        user_id=recipient_id,
        event='order_cancelled',
        title='Заказ отменён',
        message=f'Заказ #{order.id} был отменён. Причина: {cancellation_reason or "не указана"}',
        notification_type='in_app',
        data={
            'order_id': order.id,
            'cancelled_by': request.user.id
        }
    )
    
    buyer = get_user(order.buyer_id)
    seller = get_user(order.seller_id)
    
    response_data = {
        'id': order.id,
        'status': order.status,
        'gig': {
            'id': order.gig.id,
            'title': order.gig.title,
            'slug': order.gig.slug,
        },
        'package': {
            'type': order.package.type,
            'name': order.package.name,
            'price': float(order.package.price),
            'delivery_time': order.package.delivery_time,
        },
        'buyer_id': order.buyer_id,
        'seller_id': order.seller_id,
        'buyer': buyer,
        'seller': seller,
        'cancellation_reason': cancellation_reason,
        'price': float(order.price),
        'delivery_time': order.delivery_time,
        'requirements': order.requirements,
        'deadline': order.deadline.isoformat(),
        'delivered_at': order.delivered_at.isoformat() if order.delivered_at else None,
        'completed_at': order.completed_at.isoformat() if order.completed_at else None,
        'is_overdue': order.is_overdue(),
        'can_be_cancelled': order.can_be_cancelled(),
        'can_be_delivered': order.can_be_delivered(),
        'can_be_completed': order.can_be_completed(),
        'created_at': order.created_at.isoformat(),
        'updated_at': order.updated_at.isoformat(),
    }
    
    logger.info(f'Order cancelled: {order.id} by user {request.user.id}')
    
    return JsonResponse({
        'success': True,
        'message': 'Заказ отменен',
        'data': response_data
    }, status=200)


@require_http_methods(['POST'])
def dispute_create(request, order_id):
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    
    order = get_object_or_404(Order, id=order_id)
    
    if order.buyer_id != request.user.id and order.seller_id != request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'У вас нет прав для создания спора по этому заказу'
        }, status=403)
    
    if order.status not in ['in_progress', 'delivered']:
        return JsonResponse({
            'success': False,
            'error': 'Cпор можно создать только для заказов в статусе "в работе" или "доставлен"'
        }, status=400)
    
    if hasattr(order, 'dispute'):
        return JsonResponse({
            'success': False,
            'error': 'Спор по этому заказу уже существует'
        }, status=400)
    
    reason = data.get('reason')
    
    if not reason or len(reason) < 20:
        return JsonResponse({
            'success': False,
            'error': 'Причина обязательна для заполнения (минимум 20 символов)'
        }, status=400)
    
    dispute = Dispute.objects.create(
        order=order,
        created_by_id=request.user.id,
        reason=reason,
        status='open'
    )
    
    order.status = 'disputed'
    order.save(update_fields=['status', 'updated_at'])
    
    DisputeMessage.objects.create(
        dispute=dispute,
        sender_id=request.user.id,
        message=reason,
        is_moderator=False
    )
    
    recipient_id = order.seller_id if request.user.id == order.buyer_id else order.buyer_id
    
    send_notification(
        user_id=recipient_id,
        event='dispute_created',
        title='Создан спор по заказу',
        message=f'По заказу #{order.id} создан спор. Требуется ваше участие.',
        notification_type='in_app',
        data={
            'order_id': order.id,
            'dispute_id': dispute.id,
            'created_by': request.user.id
        }
    )
    
    logger.info(f'Dispute created: {dispute.id} for order {order.id}')
    
    return JsonResponse({
        'success': True,
        'message': 'Спор создан',
        'dispute_id': dispute.id
    }, status=201)
    
@require_http_methods(['GET'])
def dispute_list(request):
    role = request.GET.get('role', 'participant')
    status = request.GET.get('status')
    
    disputes = Dispute.objects.all()
    
    if role == 'participant':
        disputes = disputes.filter(
            Q(order__buyer_id=request.user.id) |
            Q(order__seller_id=request.user.id)
        )
    elif role == 'moderator':
        user_data = get_user(request.user.id)
        if not user_data or not user_data.get('is_moderator'):
            return JsonResponse({
                'success': False,
                'error': 'У вас нет прав модератора'
            }, status=403)
    
    if status:
        disputes = disputes.filter(status=status)
    
    disputes = disputes.order_by('-created_at').select_related('order', 'order__gig')
    
    user_ids = set()
    for dispute in disputes:
        user_ids.add(dispute.created_by_id)
        user_ids.add(dispute.order.buyer_id)
        user_ids.add(dispute.order.seller_id)
        if dispute.resolved_by_id:
            user_ids.add(dispute.resolved_by_id)
    
    users_data = get_users_batch(list(user_ids))
    users_map = {u['id']: u for u in users_data}
    
    data = []
    for dispute in disputes:
        created_by = users_map.get(dispute.created_by_id)
        buyer = users_map.get(dispute.order.buyer_id)
        seller = users_map.get(dispute.order.seller_id)
        resolved_by = users_map.get(dispute.resolved_by_id) if dispute.resolved_by_id else None
        
        messages_count = dispute.messages.count()
        
        dispute_data = {
            'id': dispute.id,
            'order': {
                'id': dispute.order.id,
                'gig': {
                    'id': dispute.order.gig.id,
                    'title': dispute.order.gig.title,
                    'slug': dispute.order.gig.slug,
                },
                'buyer_id': dispute.order.buyer_id,
                'seller_id': dispute.order.seller_id,
                'status': dispute.order.status,
            },
            'created_by_id': dispute.created_by_id,
            'created_by': created_by,
            'buyer': buyer,
            'seller': seller,
            'reason': dispute.reason,
            'status': dispute.status,
            'winner_side': dispute.winner_side if dispute.winner_side else None,
            'resolution': dispute.resolution if dispute.resolution else None,
            'resolved_by_id': dispute.resolved_by_id,
            'resolved_by': resolved_by,
            'resolved_at': dispute.resolved_at.isoformat() if dispute.resolved_at else None,
            'messages_count': messages_count,
            'created_at': dispute.created_at.isoformat(),
            'updated_at': dispute.updated_at.isoformat(),
        }
        
        data.append(dispute_data)
        
    return JsonResponse({
        'success': True,
        'role': role,
        'count': len(data),
        'data': data
    }, status=200)

@require_http_methods(['GET'])
def dispute_detail(request, dispute_id):
    dispute = get_object_or_404(
        Dispute.objects.select_related('order', 'order__gig'),
        id=dispute_id
    )
    
    is_participant = (
        dispute.order.buyer_id == request.user.id or
        dispute.order.seller_id == request.user.id
    )
    
    if not is_participant:
        user_data = get_user(request.user.id)
        is_moderator = user_data and user_data.get('is_moderator', False)
        
        if not is_moderator:
            return JsonResponse({
                'success': False,
                'error': 'У вас нет доступа к этому спору'
            }, status=403)
    
    messages = dispute.messages.all().order_by('created_at')
    
    user_ids = set()
    user_ids.add(dispute.created_by_id)
    user_ids.add(dispute.order.buyer_id)
    user_ids.add(dispute.order.seller_id)
    if dispute.resolved_by_id:
        user_ids.add(dispute.resolved_by_id)
    
    for message in messages:
        user_ids.add(message.sender_id)
    
    users_data = get_users_batch(list(user_ids))
    users_map = {u['id']: u for u in users_data}
    
    created_by = users_map.get(dispute.created_by_id)
    buyer = users_map.get(dispute.order.buyer_id)
    seller = users_map.get(dispute.order.seller_id)
    resolved_by = users_map.get(dispute.resolved_by_id) if dispute.resolved_by_id else None

    messages_data = []
    for message in messages:
        sender = users_map.get(message.sender_id)
        messages_data.append({
            'id': message.id,
            'sender_id': message.sender_id,
            'sender': sender,
            'message': message.message,
            'is_moderator': message.is_moderator,
            'created_at': message.created_at.isoformat(),
        })

    response_data = {
        'id': dispute.id,
        'order': {
            'id': dispute.order.id,
            'gig': {
                'id': dispute.order.gig.id,
                'title': dispute.order.gig.title,
                'slug': dispute.order.gig.slug,
            },
            'buyer_id': dispute.order.buyer_id,
            'seller_id': dispute.order.seller_id,
            'price': float(dispute.order.price),
            'status': dispute.order.status,
            'created_at': dispute.order.created_at.isoformat(),
        },
        'created_by_id': dispute.created_by_id,
        'created_by': created_by,
        'buyer': buyer,
        'seller': seller,
        'reason': dispute.reason,
        'status': dispute.status,
        'winner_side': dispute.winner_side if dispute.winner_side else None,
        'resolution': dispute.resolution if dispute.resolution else None,
        'resolved_by_id': dispute.resolved_by_id,
        'resolved_by': resolved_by,
        'resolved_at': dispute.resolved_at.isoformat() if dispute.resolved_at else None,
        'messages': messages_data,
        'messages_count': len(messages_data),
        'can_be_resolved': dispute.can_be_resolved(),
        'created_at': dispute.created_at.isoformat(),
        'updated_at': dispute.updated_at.isoformat(),
    }
    
    return JsonResponse({
        'success': True,
        'data': response_data
    }, status=200)
    
@require_http_methods(['POST'])
def dispute_add_message(request, dispute_id):
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    
    dispute = get_object_or_404(Dispute.objects.select_related('order', 'order__gig'), id=dispute_id)
    
    is_participant = (
        dispute.order.buyer_id == request.user.id or
        dispute.order.seller_id == request.user.id
    )
    
    user_data = get_user(request.user.id)
    is_moderator = user_data and user_data.get('is_moderator', False)
    
    if not is_participant and not is_moderator:
        return JsonResponse({
            'success': False,
            'error': 'У вас нет доступа к этому спору'
        }, status=403)
        
    if dispute.status == 'closed':
        return JsonResponse({
            'success': False,
            'error': 'Спор закрыт, добавление сообщений невозможно'
        }, status=400)
    
    message = data.get('message', '').strip()
    if len(message) < 5:
        return JsonResponse({
            'success': False,
            'error': 'Сообщение должно содержать минимум 5 символов'
        }, status=400)
    
    if len(message) > 1000:
        return JsonResponse({
            'success': False,
            'error': 'Сообщение не должно превышать 1000 символов'
        }, status=400)
        
    dispute_message = DisputeMessage.objects.create(
        dispute=dispute,
        sender_id=request.user.id,
        message=message,
        is_moderator=is_moderator
    )
    
    dispute.updated_at = timezone.now()
    dispute.save(update_fields=['updated_at'])
    
    recipients = []
    
    if request.user.id != dispute.order.buyer_id:
        recipients.append(dispute.order.buyer_id)
    
    if request.user.id != dispute.order.seller_id:
        recipients.append(dispute.order.seller_id)
    
    for recipient_id in recipients:
        send_notification(
            user_id=recipient_id,
            event='dispute_message',
            title='Новое сообщение в споре',
            message=f'Новое сообщение по спору #{dispute.id} для заказа #{dispute.order.id}',
            notification_type='in_app',
            data={
                'dispute_id': dispute.id,
                'order_id': dispute.order.id,
                'sender_id': request.user.id
            }
        )
    
    logger.info(f'Message added to dispute {dispute_id} by user {request.user.id}')
    
    sender = user_data
    
    response_data = {
        'message': {
            'id': dispute_message.id,
            'sender_id': dispute_message.sender_id,
            'sender': sender,
            'message': dispute_message.message,
            'is_moderator': dispute_message.is_moderator,
            'created_at': dispute_message.created_at.isoformat(),
        },
        'dispute': {
            'id': dispute.id,
            'status': dispute.status,
            'messages_count': dispute.messages.count(),
            'updated_at': dispute.updated_at.isoformat(),
        }
    }
    
    return JsonResponse({
        'success': True,
        'message': 'Сообщение добавлено',
        'data': response_data
    }, status=201)

@require_http_methods(['POST'])
def dispute_resolve(request, dispute_id):
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    
    dispute = get_object_or_404(Dispute.objects.select_related('order', 'order__gig'), id=dispute_id)
    
    user_data = get_user(request.user.id)
    is_moderator = user_data and user_data.get('is_moderator', False)
    
    if not is_moderator:
        return JsonResponse({
            'success': False,
            'error': 'Только модератор может разрешить спор.'
        }, status=403)

    if not dispute.can_be_resolved():
        return JsonResponse({
            'success': False,
            'error': 'Спор уже решён или закрыт'
        }, status=400)
    
    winner_side = data.get('winner_side', '').strip()
    resolution = data.get('resolution', '').strip()
    
    if not winner_side or not resolution:
        return JsonResponse({
            'success': False,
            'error': 'Необходимо указать winner_side и resolution'
        }, status=400)
    
    if winner_side not in ['buyer', 'seller']:
        return JsonResponse({
            'success': False,
            'error': 'winner_side должен быть "buyer" или "seller"'
        }, status=400)
    
    if len(resolution) < 20:
        return JsonResponse({
            'success': False,
            'error': 'Решение должно содержать минимум 20 символов'
        }, status=400)
    
    dispute.status = 'resolved'
    dispute.resolved_by_id = request.user.id
    dispute.resolution = resolution
    dispute.winner_side = winner_side
    dispute.resolved_at = timezone.now()
    dispute.save()
    
    order = dispute.order
    
    if winner_side == 'buyer':
        order.status = 'cancelled'
        order.save(update_fields=['status', 'updated_at'])
    elif winner_side == 'seller':
        order.status = 'completed'
        order.completed_at = timezone.now()
        order.save(update_fields=['status', 'completed_at', 'updated_at'])
        
        order.gig.orders_count += 1
        order.gig.save(update_fields=['orders_count'])
    
    winner_text = "покупателя" if winner_side == "buyer" else "продавца"
    DisputeMessage.objects.create(
        dispute=dispute,
        sender_id=request.user.id,
        message=f'Спор решён в пользу {winner_text}. Решение: {resolution}',
        is_moderator=True
    )
    
    send_notification(
        user_id=order.buyer_id,
        event='dispute_resolved',
        title='Спор решён',
        message=f'Модератор принял решение по спору #{dispute.id}. Победитель: {"вы" if winner_side == "buyer" else "продавец"}',
        notification_type='in_app',
        data={
            'dispute_id': dispute.id,
            'order_id': order.id,
            'winner_side': winner_side
        }
    )
    
    send_notification(
        user_id=order.seller_id,
        event='dispute_resolved',
        title='Спор решён',
        message=f'Модератор принял решение по спору #{dispute.id}. Победитель: {"покупатель" if winner_side == "buyer" else "вы"}',
        notification_type='in_app',
        data={
            'dispute_id': dispute.id,
            'order_id': order.id,
            'winner_side': winner_side
        }
    )
    
    logger.info(f'Dispute resolved: {dispute.id} by moderator {request.user.id}, winner: {winner_side}')
    
    buyer = get_user(order.buyer_id)
    seller = get_user(order.seller_id)
    moderator = user_data
    
    response_data = {
        'id': dispute.id,
        'order': {
            'id': order.id,
            'status': order.status,
            'completed_at': order.completed_at.isoformat() if order.completed_at else None,
        },
        'status': dispute.status,
        'winner_side': dispute.winner_side,
        'resolution': dispute.resolution,
        'resolved_by_id': dispute.resolved_by_id,
        'resolved_by': moderator,
        'resolved_at': dispute.resolved_at.isoformat(),
        'buyer': buyer,
        'seller': seller,
        'updated_at': dispute.updated_at.isoformat(),
    }
    
    return JsonResponse({
        'success': True,
        'message': 'Спор успешно решён',
        'data': response_data
    }, status=200)
