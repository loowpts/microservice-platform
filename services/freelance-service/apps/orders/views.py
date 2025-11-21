import json
import logging
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Sum, Count, Avg

from apps.gigs.models import Gig, GigPackage
from apps.common.api import get_user, get_users_batch
from apps.orders.models import Order
from apps.reviews.models import Review
from .models import Order, OrderDelivery, OrderRequirement
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
