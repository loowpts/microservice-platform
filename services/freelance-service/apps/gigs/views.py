import json
import logging
from django.db.models import Q, Min, Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from apps.common.api import get_user, get_users_batch
from apps.gigs.forms import GigForm, GigPackageForm
from apps.gigs.models import Gig, GigPackage, GigImage

logger = logging.getLogger(__name__)


@require_http_methods(['GET'])
def gig_list(request):
    try:
        category_id = request.GET.get('category')
        subcategory_id = request.GET.get('subcategory')
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        search = request.GET.get('search', '').strip()
        sort_by = request.GET.get('sort_by', '-created_at')
        
        gigs = Gig.objects.filter(status='active')
        
        if category_id:
            gigs = gigs.filter(category_id=category_id)
        if subcategory_id:
            gigs = gigs.filter(subcategory_id=subcategory_id)
        if min_price:
            gigs = gigs.filter(packages__price__gte=min_price)
        if max_price:
            gigs = gigs.filter(packages__price__lte=max_price)
        if search:
            gigs = gigs.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
        
        allowed_sort_fields = ['-created_at', 'price', '-rating_average', '-orders_count']
        
        if sort_by == 'price':
            gigs = gigs.annotate(price=Min('packages__price')).order_by('price')
        else:
            gigs = gigs.order_by(sort_by)

        gigs = gigs.distinct()
        gigs = gigs.select_related('category').prefetch_related('packages')
                
            
        seller_ids = gigs.values_list('seller_id', flat=True).distinct()
        sellers_data = get_users_batch(seller_ids)
        sellers_map = {u['id']: u for u in sellers_data}
        
        data = []
        for gig in gigs:
            seller = sellers_map.get(gig.seller_id)
            min_price_value = gig.packages.aggregate(min_price=Min('price'))['min_price']
            
            data.append({
                'id': gig.id,
                'title': gig.title,
                'slug': gig.slug,
                'description': (gig.description[:200] + '...') if gig.description and len(gig.description) > 200 else gig.description,
                'main_image': gig.main_image.url if gig.main_image else None,
                'category': {
                    'id': gig.category.id if gig.category else None,
                    'name': gig.category.name if gig.category else None,
                },
                'seller_id': gig.seller_id,
                'seller': seller,
                'min_price': min_price_value,
                'rating': gig.rating_average,
                'reviews_count': gig.reviews_count,
                'orders_count': gig.orders_count,
                'created_at': gig.created_at.isoformat() if gig.created_at else None,
            })
    
        return JsonResponse({
            'success': True,
            'count': len(data),
            'data': data
        }, status=200)
        
    except Exception as e:
        logger.exception('Ошибка при получении списка услуг.')
        return JsonResponse({
            'success': False,
            'error': str(e),
        }, status=500)


@require_http_methods(['GET'])
def gig_detail(request, slug):
    gig = get_object_or_404(Gig, slug=slug, status='active')
    
    gig.views_count += 1
    gig.save(update_fields=['views_count'])
    
    
    sellers_data = get_user(gig.seller_id)
    
    
    packages = gig.packages.all()
    packages_list = [{
        'package_type': p.package_type,
        'name': p.name,
        'description': p.description,
        'price': p.price,
        'delivery_time': p.delivery_time,
        'revisions': p.revisions,
        'features': p.features,
    } for p in packages]
    
    images = gig.images.all()
    images_list = [{
        'id': img.id,
        'image_url': img.image_url,
        'is_primary': img.is_primary,
        'caption': img.caption,
    } for img in images]
    
    tags = [t.tag for t in gig.tags.all()]
    
    response_data = {
        'id': gig.id,
        'title': gig.title,
        'slug': gig.slug,
        'description': gig.description,
        'main_image': gig.main_image.url if gig.main_image else None,
        'status': gig.status,
        'rating_average': gig.rating_average,
        'reviews_count': gig.reviews_count,
        'orders_count': gig.orders_count,
        'views_count': gig.views_count,
        'created_at': gig.created_at.isoformat() if gig.created_at else None,
        'updated_at': gig.updated_at.isoformat() if gig.updated_at else None,
        
        'seller': {
            'id': gig.seller_id,
            'email': sellers_data.get('email', ''),
            'avatar_url': sellers_data.get('avatar_url'),
        } if sellers_data else None,

        'packages': packages_list,
        'images': images_list,
        'tags': tags,

        'category': {
            'id': gig.category.id,
            'name': gig.category.name,
        } if getattr(gig, 'category', None) else None,

        'subcategory': {
            'id': gig.subcategory.id,
            'name': gig.subcategory.name,
        } if getattr(gig, 'subcategory', None) else None,
    }
    
    logger.info(f"Gig viewed: {gig.id} ({gig.slug}) by {request.user.id}")
    
    return JsonResponse({
        'success': True,
        'data': response_data
    }, status=200)
    
@require_http_methods(['POST'])
def gig_create(request):
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Невалидный Json'
        }, status=400)
        
    form = GigForm(data)
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'error': form.errors
        }, status=400)
        
    gig = form.save(commit=False)
    gig.seller_id = request.user.id
    gig.status = 'draft'
    gig.save()
    
    seller_data = get_user(gig.seller_id)
    
    response_data = {
        'id': gig.id,
        'title': gig.title,
        'slug': gig.slug,
        'description': gig.description,
        'category': {
            'id': gig.category.id if gig.category else None,
            'name': gig.category.name if gig.category else None,
            'slug': gig.category.slug if gig.category else None,
        } if gig.category else None,
        
        'status': gig.status,
        'views_count': gig.views_count,
        'orders_count': gig.orders_count,
        'rating_average': gig.rating_average,
        'reviews_count': gig.reviews_count,
        'seller_id': gig.seller_id,
        'seller': seller_data,
        'main_image': gig.main_image,
        'created_at': gig.created_at.isoformat(),
        'updated_at': gig.updated_at.isoformat(),
    }
    
    logger.info(f'Gig created: {gig.id} by user {request.user.id}')
    
    images_urls = data.get('images')
    
    if isinstance(images_urls, list):
        GigImage.objects.filter(gig=gig).delete()
        
        for i, url in enumerate(images_urls):
            GigImage.objects.create(
                gig=gig,
                image_url=url,
                order=i
            )
            
    seller_data = get_user(gig.seller_id)
    return JsonResponse({
        'success': True,
        'message': 'Услуга успешно создана',
        'data': response_data
    }, status=201)

@require_http_methods(['PUT'])
def gig_update(request, slug):
    gig = get_object_or_404(Gig, slug=slug)
    
    if gig.seller_id != request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'У вас нету прав для редактирования.'
        }, status=403)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Невалидный Json'
        }, status=403)
    
    form = GigForm(data, instance=gig)
    
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'error': form.errors,
        }, status=400)
    
    form.save()
    
    images_urls = data.get('images')

    if isinstance(images_urls, list):
        GigImage.objects.filter(gig=gig).delete()
        
        for i, url in enumerate(images_urls):
            GigImage.objects.create(
                gig=gig,
                image_url=url,
                order=i
            )
            
    seller_data = get_user(gig.seller_id)
    
    response_data = {
        'id': gig.id,
        'title': gig.title,
        'slug': gig.slug,
        'description': gig.description,
        'category': {
            'id': gig.category.id if gig.category else None,
            'name': gig.category.name if gig.category else None,
            'slug': gig.category.slug if gig.category else None,
        } if gig.category else None,
        
        'status': gig.status,
        'views_count': gig.views_count,
        'orders_count': gig.orders_count,
        'rating_average': gig.rating_average,
        'reviews_count': gig.reviews_count,
        'seller_id': gig.seller_id,
        'seller': seller_data,
        'main_image': gig.main_image,
        'created_at': gig.created_at.isoformat(),
        'updated_at': gig.updated_at.isoformat(),
    }
    
    return JsonResponse({
        'success': True,
        'message': 'Услуга успешно обновлена',
        'data': response_data
    }, status=200)

@require_http_methods(['DELETE'])
def gig_delete(request, slug):
    gig = get_object_or_404(Gig, slug=slug)
    
    if gig.seller_id != request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'У вас нет прав для удаления'
        }, status=403)
        
    gig.delete()
    
    logger.info(f'Gig deleted: {gig.id} by user {request.user.id}')
    
    return JsonResponse({
        'success': True,
        'message': 'Услуга успешно удалена'
    }, status=200)

    
@require_http_methods(['PATCH'])
def gig_status_update(request, slug):
    gig = get_object_or_404(Gig, slug=slug)
    
    if gig.seller_id != request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'У вас нету прав для удаления'
        }, status=403)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Невалидный Json'
        }, status=403)
        
    new_status = data.get('status')
    
    if not new_status in ['draft', 'pending_approval', 'active', 'paused', 'archived']:
        return JsonResponse({
            'success': False,
            'error': 'Недопустимый статус'
        }, status=400)
    
    gig.status = new_status
    gig.save(update_fields=['status', 'updated_at'])
    
    logger.info(f'New status: {gig.status} by user {request.user.id}')
    
    return JsonResponse({
        'success': True,
        'message': 'Статус успешно обновлён',
        'status': new_status
    }, status=200)
    
@require_http_methods(['GET'])
def my_gigs(request):
    status = request.GET.get('status')
    gigs = (
        Gig.objects.filter(seller_id=request.user.id)
        .prefetch_related(
            Prefetch('packages', queryset=GigPackage.objects.all()),
            'category'
        )
        .order_by('-created_at')
    )
    
    if status:
        gigs = gigs.filter(status=status)
    
    gigs_data = []
    for gig in gigs:
        packages = gig.packages.all()
        min_price = packages.aggregate(Min('price'))['price__min']
        packages_count = packages.count()
        
        gigs_data.append({
            'id': gig.id,
            'title': gig.title,
            'slug': gig.slug,
            'category': gig.category.name if gig.category else None,
            'status': gig.status,
            'created_at': gig.created_at,
            'updated_at': gig.updated_at,
            'min_price': min_price,
            'packages_count': packages_count,
        })
        
    return JsonResponse({
        'success': True,
        'count': len(gigs_data),
        'data': gigs_data
    })
        
@require_http_methods(['POST'])
def package_create(request, slug):
    gig = get_object_or_404(Gig, slug=slug)
    
    if gig.seller_id != request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'У вас нету прав.'
        }, status=403)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Невалидный Json'
        }, status=400)
    
    form = GigPackageForm(data)
    
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'error': form.errors
        }, status=400)
    
    package_type = form.cleaned_data.get("package_type")
    if GigPackage.objects.filter(gig=gig, package_type=package_type).exists():
        return JsonResponse(
            {
                "success": False,
                "message": f"Пакет типа '{package_type}' уже существует для этой услуги"
            },
            status=400
        )
    
    package = form.save(commit=False)
    package.gig = gig
    package.save()
        
    response_data = {
        "id": package.id,
        "gig_id": gig.id,
        "package_type": package.package_type,
        "name": package.name,
        "description": package.description,
        "price": package.price,
        "delivery_time": package.delivery_time,
        "revisions": package.revisions,
        "features": package.features,
        "created_at": package.created_at.isoformat() if package.created_at else None,
        "updated_at": package.updated_at.isoformat() if package.updated_at else None,
    }

    logger.info(f"Пакет '{package.package_type}' создан пользователем {request.user.id} для gig '{gig.slug}'")

    return JsonResponse(
        {
            "success": True,
            "message": "Пакет успешно добавлен",
            "data": response_data,
        },
        status=201
    )

@require_http_methods(['PUT'])
def package_update(request, slug, package_id):
    gig = get_object_or_404(Gig, slug=slug)
    
    if gig.seller_id != request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'У вас нету прав доступа.'
        }, status=403)
    
    package = get_object_or_404(GigPackage, id=package_id, gig=gig)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Невалидный Json'
        }, status=400)
    
    form = GigPackageForm(data, instance=package)
    
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'error': form.errors
        }, status=400)
        
    form.save()
    
    response_data = {
        "id": package.id,
        "gig_id": gig.id,
        "package_type": package.package_type,
        "title": package.name,
        "description": package.description,
        "price": package.price,
        "delivery_time": package.delivery_time,
    }
    
    logger.info(f'GigPackage: {package.package_type} ID({package.id}) updated for user {request.user.id}')
    
    return JsonResponse({
        'success': True,
        'message': 'Пакет успешно обновлён',
        'data': response_data
    }, status=200)
    
@require_http_methods(['DELETE'])
def package_delete(request, slug, package_id):
    gig = get_object_or_404(Gig, slug=slug)
    
    if gig.seller_id != request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'У вас нет прав доступа'
        }, status=400)
    
    package = get_object_or_404(GigPackage, id=package_id, gig=gig)

    logger.info(f'Deleted package {package.name} ID({package.id}) by user {request.user.id}')
    
    package.delete()
    
    return JsonResponse({
        'success': True,
        'message': 'Пакет успешно удалён'
    }, status=200)
