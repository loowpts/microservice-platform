import logging
import csv
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Sum, Count, Avg
from django.db.models.functions import TruncDate

from apps.gigs.models import Gig
from apps.orders.models import Order
from apps.reviews.models import Review


logger = logging.getLogger(__name__)

@require_http_methods(['GET'])
def analytics_dashboard(request):
    """Общая статистика фрилансера (дашборд)"""
    
    period = request.GET.get('period', '30')
    
    gigs = Gig.objects.filter(seller_id=request.user.id, status='active')
    total_gigs = gigs.count()
    total_packages = gigs.aggregate(packages=Count('packages'))['packages'] or 0
    
    orders = Order.objects.filter(seller_id=request.user.id)
    
    # Применяем фильтр по периоду
    if period != 'all':
        try:
            period_days = int(period)
            date_from = timezone.now() - timedelta(days=period_days)
            orders = orders.filter(created_at__gte=date_from)
        except ValueError:
            logger.warning(f'Invalid period: {period}')
    
    # Подсчёт заказов
    total_orders = orders.count()
    completed_orders = orders.filter(status='completed').count()
    active_orders = orders.filter(status__in=['pending', 'in_progress']).count()
    cancelled_orders = orders.filter(status='cancelled').count()
    
    # Финансовая статистика
    total_revenue = orders.filter(status='completed').aggregate(
        total=Sum('price')
    )['total'] or 0
    
    average_order_value = orders.filter(status='completed').aggregate(
        avg=Avg('price')
    )['avg'] or 0
    
    pending_revenue = orders.filter(
        status__in=['pending', 'in_progress']
    ).aggregate(total=Sum('price'))['total'] or 0
    
    # Статистика по отзывам
    reviews = Review.objects.filter(seller_id=request.user.id)
    
    # Применяем фильтр по периоду для отзывов
    if period != 'all':
        try:
            period_days = int(period)
            date_from = timezone.now() - timedelta(days=period_days)
            reviews = reviews.filter(created_at__gte=date_from)
        except ValueError:
            pass
    
    total_reviews = reviews.count()
    average_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    
    # Распределение по рейтингу
    five_stars = reviews.filter(rating=5).count()
    four_stars = reviews.filter(rating=4).count()
    three_stars = reviews.filter(rating=3).count()
    two_stars = reviews.filter(rating=2).count()
    one_star = reviews.filter(rating=1).count()
    
    # Статистика по просмотрам
    total_views = gigs.aggregate(views=Sum('views_count'))['views'] or 0
    
    # Топ услуги по заказам
    top_gigs_by_orders = gigs.annotate(
        orders_count=Count('orders')
    ).order_by('-orders_count')[:3]
    
    top_gigs_orders = [
        {
            'id': gig.id,
            'title': gig.title,
            'slug': gig.slug,
            'orders_count': gig.orders_count
        }
        for gig in top_gigs_by_orders
    ]
    
    # Топ услуги по доходу
    top_gigs_by_revenue = gigs.annotate(
        revenue=Sum('orders__price', filter=Q(orders__status='completed'))
    ).order_by('-revenue')[:3]
    
    top_gigs_revenue = [
        {
            'id': gig.id,
            'title': gig.title,
            'slug': gig.slug,
            'revenue': float(gig.revenue) if gig.revenue else 0
        }
        for gig in top_gigs_by_revenue
    ]
    
    overview = {
        'total_gigs': total_gigs,
        'total_packages': total_packages,
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'active_orders': active_orders,
        'cancelled_orders': cancelled_orders,
        'total_revenue': float(total_revenue),
        'average_order_value': float(average_order_value),
        'pending_revenue': float(pending_revenue),
        'total_reviews': total_reviews,
        'average_rating': float(average_rating),
        'total_views': total_views
    }
    
    rating_distribution = {
        'five_stars': five_stars,
        'four_stars': four_stars,
        'three_stars': three_stars,
        'two_stars': two_stars,
        'one_star': one_star
    }
    
    logger.info(f'Analytics dashboard viewed by user {request.user.id}, period={period}')
    
    return JsonResponse({
        'success': True,
        'period': period,
        'overview': overview,
        'rating_distribution': rating_distribution,
        'top_gigs_by_orders': top_gigs_orders,
        'top_gigs_by_revenue': top_gigs_revenue
    })
    
    
@require_http_methods(['GET'])
def analytics_gig_stats(request, slug):
    """Детальная статистика по конкретной услуге"""
    
    period = request.GET.get('period', '30')
    
    gig = get_object_or_404(Gig, slug=slug, seller_id=request.user.id)
    
    gig_info = {
        'id': gig.id,
        'title': gig.title,
        'slug': gig.slug,
        'status': gig.status,
        'created_at': gig.created_at.isoformat(),
        'views_count': gig.views_count,
        'favorites_count': gig.favorites_count if hasattr(gig, 'favorites_count') else 0
    }
    
    orders = Order.objects.filter(gig=gig)
    
    # Фильтр по периоду
    if period != 'all':
        try:
            period_days = int(period)
            date_from = timezone.now() - timedelta(days=period_days)
            orders = orders.filter(created_at__gte=date_from)
        except ValueError:
            logger.warning(f'Invalid period: {period}')
    
    # Подсчёт заказов
    total_orders = orders.count()
    completed_orders = orders.filter(status='completed').count()
    active_orders = orders.filter(status__in=['pending', 'in_progress']).count()
    cancelled_orders = orders.filter(status='cancelled').count()
    
    # Процент завершённых заказов
    completion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0
    
    orders_stats = {
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'active_orders': active_orders,
        'cancelled_orders': cancelled_orders,
        'completion_rate': round(completion_rate, 2)
    }
    
    # Финансовая статистика
    total_revenue = orders.filter(status='completed').aggregate(
        total=Sum('price')
    )['total'] or 0
    
    average_order_value = orders.filter(status='completed').aggregate(
        avg=Avg('price')
    )['avg'] or 0
    
    pending_revenue = orders.filter(
        status__in=['pending', 'in_progress']
    ).aggregate(total=Sum('price'))['total'] or 0
    
    revenue_stats = {
        'total_revenue': float(total_revenue),
        'average_order_value': float(average_order_value),
        'pending_revenue': float(pending_revenue)
    }
    
    # Статистика по пакетам
    packages = gig.packages.all()
    packages_stats = []
    
    for package in packages:
        package_orders = orders.filter(package_type=package.type)
        package_orders_count = package_orders.count()
        package_revenue = package_orders.filter(
            status='completed'
        ).aggregate(sum=Sum('price'))['sum'] or 0
        
        packages_stats.append({
            'type': package.type,
            'name': package.name,
            'price': float(package.price),
            'orders_count': package_orders_count,
            'revenue': float(package_revenue)
        })
    
    # Статистика по отзывам
    reviews = Review.objects.filter(gig=gig)
    
    # Применяем фильтр по периоду для отзывов
    if period != 'all':
        try:
            period_days = int(period)
            date_from = timezone.now() - timedelta(days=period_days)
            reviews = reviews.filter(created_at__gte=date_from)
        except ValueError:
            pass
    
    total_reviews = reviews.count()
    average_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    
    # Распределение по рейтингу
    five_stars = reviews.filter(rating=5).count()
    four_stars = reviews.filter(rating=4).count()
    three_stars = reviews.filter(rating=3).count()
    two_stars = reviews.filter(rating=2).count()
    one_star = reviews.filter(rating=1).count()
    
    reviews_stats = {
        'total_reviews': total_reviews,
        'average_rating': float(average_rating),
        'rating_distribution': {
            'five_stars': five_stars,
            'four_stars': four_stars,
            'three_stars': three_stars,
            'two_stars': two_stars,
            'one_star': one_star
        }
    }
    
    # Конверсия (просмотры -> заказы)
    conversion_rate = (total_orders / gig.views_count * 100) if gig.views_count > 0 else 0
    
    # Последние заказы
    recent_orders = orders.order_by('-created_at')[:5]
    recent_orders_data = [
        {
            'id': order.id,
            'buyer_id': order.buyer_id,
            'status': order.status,
            'price': float(order.price),
            'created_at': order.created_at.isoformat()
        }
        for order in recent_orders
    ]
    
    logger.info(f'Gig stats viewed: {gig.slug} by user {request.user.id}')
    
    return JsonResponse({
        'success': True,
        'period': period,
        'gig': gig_info,
        'orders': orders_stats,
        'revenue': revenue_stats,
        'packages': packages_stats,
        'reviews': reviews_stats,
        'conversion_rate': round(conversion_rate, 2),
        'recent_orders': recent_orders_data
    })


@require_http_methods(['GET'])
def analytics_revenue_chart(request):
    """График дохода по дням/месяцам"""
    period = request.GET.get('period', '30')
    grouping = request.GET.get('grouping', 'day')
    
    date_from = timezone.now() - timedelta(days=int(period))
    orders = Order.objects.filter(
        seller_id=request.user.id,
        status='completed',
        created_at__gte=date_from
    )
    
    revenue_by_date = orders.annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        revenue=Sum('price'),
        orders=Count('id')
    ).order_by('date')
    
    data = [
        {
            'date': item['date'].isoformat(),
            'revenue': float(item['revenue']),
            'orders': item['orders']
        }
        for item in revenue_by_date
    ]
    
    return JsonResponse({
        'success': True,
        'period': period,
        'grouping': grouping,
        'data': data
    })


@require_http_methods(['GET'])
def analytics_compare(request):
    """Сравнить текущий период с предыдущим"""
    period = int(request.GET.get('period', '30'))
    
    # Текущий период
    current_end = timezone.now()
    current_start = current_end - timedelta(days=period)
    
    # Предыдущий период
    previous_end = current_start
    previous_start = previous_end - timedelta(days=period)
    
    current_orders = Order.objects.filter(
        seller_id=request.user.id,
        created_at__gte=current_start,
        created_at__lt=current_end
    )
    
    previous_orders = Order.objects.filter(
        seller_id=request.user.id,
        created_at__gte=previous_start,
        created_at__lt=previous_end
    )
    
    # Сравнение метрик
    current_revenue = current_orders.filter(status='completed').aggregate(Sum('price'))['price__sum'] or 0
    previous_revenue = previous_orders.filter(status='completed').aggregate(Sum('price'))['price__sum'] or 0
    
    revenue_change = ((current_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else 0
    
    return JsonResponse({
        'success': True,
        'current_period': {
            'revenue': current_revenue,
            'orders': current_orders.count()
        },
        'previous_period': {
            'revenue': previous_revenue,
            'orders': previous_orders.count()
        },
        'changes': {
            'revenue_change_percent': revenue_change
        }
    })

@require_http_methods(['GET'])
def analytics_export(request):
    """Экспортировать статистику в CSV"""
    orders = Order.objects.filter(seller_id=request.user.id)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="analytics.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Order ID', 'Gig', 'Buyer ID', 'Status', 'Price', 'Date'])
    
    for order in orders:
        writer.writerow([
            order.id,
            order.gig.title,
            order.buyer_id,
            order.status,
            order.price,
            order.created_at.strftime('%Y-%m-%d')
        ])
    
    return response
