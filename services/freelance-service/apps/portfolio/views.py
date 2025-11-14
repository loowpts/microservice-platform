import json
import logging
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from apps.common.api import get_user, get_users_batch
from .models import PortfolioItem, PortfolioImage
from .forms import PortfolioItemForm, PortfolioImageForm

logger = logging.getLogger(__name__)


@require_http_methods(['GET'])
def portfolio_list(request):
    seller_id = request.GET.get('seller_id')
    search = request.GET.get('search').strip()
    
    items = PortfolioItem.objects.all()
    
    if seller_id:
        try:
            seller_id = int(seller_id)
            items = items.filter(seller_id=seller_id)
        except ValueError:
            logger.warning(f'Invalid seller_id: {seller_id}')
            
    if search:
        items = items.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )
        
    items = items.order_by('-created_at').select_related('category').prefetch_related('images')
    
    seller_ids = list(set([item.seller_id for item in items]))
    sellers_data = get_users_batch(seller_ids)
    sellers_map = {u['id']: u for u in sellers_data}
    
    data = []
    for item in items:
        seller = sellers_map.get(item.seller_id)
        images_count = item.images.count() 
        description = item.description
        
        if description and len(description) > 150:
            description = description[:150] + '...'
        data.append({
            'id': item.id,
            'title': item.title,
            'slug': item.slug,
            'description': description,
            'main_image': item.main_image,
            'project_url': item.project_url,
            'technologies': item.technologies if item.technologies else [],
            'completion_date': item.completion_date.isoformat() if item.completion_date else None,
            'client_name': item.client_name,
            'category': {
                'id': item.category.id,
                'name': item.category.name,
                'slug': item.category.slug,
            } if item.category else None,
            'seller_id': item.seller_id,
            'seller': seller,
            'images_count': images_count,
            'views_count': item.views_count,
            'created_at': item.created_at.isoformat(),
        })
        
    return JsonResponse({
        'success': True,
        'count': len(data),
        'data': data
    })
    
@require_http_methods(['GET'])
def portfolio_detail(request, slug):
    item = get_object_or_404(PortfolioItem.objects.prefetch_related('images'), slug=slug)
    
    item.views_count += 1
    item.save(update_fields=['views_count'])
    
    seller_data = get_user(item.seller_id)
    
    images = item.images.all()
    images_list = []
    for image in images:
        images_list.append({
            'id': image.id,
            'image_url': image.image_url,
            'caption': image.caption,
            'order': image.order,
            'is_primary': image.is_primary
        })

    response_data = {
        'id': item.id,
        'title': item.title,
        'slug': item.slug,
        'description': item.description,
        'main_image': item.main_image,
        'project_url': item.project_url,
        'technologies': item.technologies if item.technologies else [],
        'completion_date': item.completion_date.isoformat() if item.completion_date else None,
        'client_name': item.client_name,
        'category': {
            'id': item.category.id,
            'name': item.category.name,
            'slug': item.category.slug,
        } if item.category else None,
        'seller_id': item.seller_id,
        'seller': seller_data,
        'images': images_list,
        'views_count': item.views_count,
        'created_at': item.created_at.isoformat(),
        'updated_at': item.updated_at.isoformat()
    }

    logger.info(f'Portfolio item viewed: {item.id}')
    
    return JsonResponse({
        'success': True,
        'data': response_data
    })
    
@require_http_methods(['POST'])
def portfolio_create(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Невалидный Json',
        }, status=400)
    
    form = PortfolioItemForm(data)
    
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)
    
    item = form.save(commit=False)
    item.seller_id = request.user.id
    item.save()
    
    seller_data = get_user(item.seller_id)
    
    response_data = {
        'id': item.id,
        'title': item.title,
        'slug': item.slug,
        'description': item.description,
        'main_image': item.main_image,
        'project_url': item.project_url,
        'technologies': item.technologies if item.technologies else [],
        'completion_date': item.completion_date.isoformat() if item.completion_date else None,
        'client_name': item.client_name,
        'category': {
            'id': item.category.id,
            'name': item.category.name,
            'slug': item.category.slug,
        } if item.category else None,
        'seller_id': item.seller_id,
        'seller': seller_data,
        'views_count': item.views_count,
        'created_at': item.created_at.isoformat(),
        'updated_at': item.updated_at.isoformat(),
    }

    logger.info(f'Portfolio item created: {item.id} by user {request.user.id}')
    
    return JsonResponse({
        'success': True,
        'message': 'Работа успешно добавлена в портфолио',
        'data': response_data
    }, status=201)


@require_http_methods(['PATCH'])
def portfolio_update(request, slug):
    item = get_object_or_404(PortfolioItem, slug=slug)
    
    if item.seller_id != request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'У вас нет прав для редактирования этой работы'
        }, status=403)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    
    form = PortfolioItemForm(data, instance=item)
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)
    
    old_title = item.title
    item = form.save(commit=False)
    
    if 'title' in data and data['title'] != old_title:
        from pytils.translit import slugify as pytils_slugify
        
        name_with_dashes = item.title.replace('_', '-')
        base_slug = pytils_slugify(name_with_dashes)
        new_slug = base_slug
        counter = 1
        
        while PortfolioItem.objects.filter(slug=new_slug).exclude(id=item.id).exists():
            new_slug = f'{base_slug}-{counter}'
            counter += 1
        
        item.slug = new_slug
    
    item.save()
    
    seller_data = get_user(item.seller_id)
    
    response_data = {
        'id': item.id,
        'title': item.title,
        'slug': item.slug,
        'description': item.description,
        'main_image': item.main_image,
        'project_url': item.project_url,
        'technologies': item.technologies if item.technologies else [],
        'completion_date': item.completion_date.isoformat() if item.completion_date else None,
        'client_name': item.client_name,
        'category': {
            'id': item.category.id,
            'name': item.category.name,
            'slug': item.category.slug,
        } if item.category else None,
        'seller_id': item.seller_id,
        'seller': seller_data,
        'views_count': item.views_count,
        'created_at': item.created_at.isoformat(),
        'updated_at': item.updated_at.isoformat(),
    }
    
    logger.info(f'Portfolio item updated: {item.id} by user {request.user.id}')
    
    return JsonResponse({
        'success': True,
        'message': 'Работа успешно обновлена',
        'data': response_data
    }, status=200)
    
@require_http_methods(['DELETE'])
def portfolio_delete(request, slug):
    item = get_object_or_404(PortfolioItem, slug=slug)
    
    if item.seller_id != request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'У вас нет прав для удаления этой работы'
        }, status=403)
    
    item_id = item.id
    logger.info(f'Portfolio item deleted: {item_id} by user {request.user.id}')
    item.delete()
    
    return JsonResponse({
        'success': True,
        'message': 'Работа успешно удалена из портфолио'
    }, status=200)   
    
@require_http_methods(['GET'])
def my_portfolio(request):
    items = PortfolioItem.objects.filter(seller_id=request.user.id)
    items = items.order_by('-created_at').prefetch_related('images')
    
    data = []
    for item in items:
        images_count = item.images.count()
        
        data.append({
            'id': item.id,
            'title': item.title,
            'slug': item.slug,
            'description': item.description,
            'main_image': item.main_image,
            'project_url': item.project_url,
            'technologies': item.technologies if item.technologies else [],
            'completion_date': item.completion_date.isoformat() if item.completion_date else None,
            'client_name': item.client_name,
            'category': {
                'id': item.category.id,
                'name': item.category.name,
                'slug': item.category.slug,
            } if item.category else None,
            'images_count': images_count,
            'views_count': item.views_count,
            'created_at': item.created_at.isoformat(),
            'updated_at': item.updated_at.isoformat(),
        })
    
    return JsonResponse({
        'success': True,
        'count': len(data),
        'data': data
    })
    

@require_http_methods(['POST'])
def portfolio_image_add(request, slug):
    item = get_object_or_404(PortfolioItem, slug=slug)
    
    if item.seller_id != request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'У вас нет прав для добавления изображений'
        }, status=403)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid Json'
        }, status=400)
    
    form = PortfolioImageForm(data)
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)
    
    image = form.save(commit=False)
    image.portfolio_item = item
    image.save()
    
    logger.info(f'Image added to portfolio item {item.id}: image {image.id}')
    
    return JsonResponse({
        'success': True,
        'message': 'Изображение успешно добавлено',
        'data': {
            'id': image.id,
            'image_url': image.image_url,
            'caption': image.caption,
            'order': image.order,
            'is_primary': image.is_primary
        }
    }, status=201)
    
@require_http_methods(['PATCH'])
def portfolio_image_update(request, slug, image_id):
    item = get_object_or_404(PortfolioItem, slug=slug)
    image = get_object_or_404(PortfolioImage, id=image_id, portfolio_item=item)

    if item.seller_id != request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'У вас нет прав для редактирования'
        }, status=403)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid Json'
        }, status=400)
    
    form = PortfolioImageForm(data, instance=image)
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)
        
    image = form.save()
    
    logger.info(f'Image updated: {image.id} in portfolio {item.id}')
    
    return JsonResponse({
        'success': True,
        'message': 'Изображение успешно обновлено',
        'data': {
            'id': image.id,
            'image_url': image.image_url,
            'caption': image.caption,
            'order': image.order,
            'is_primary': image.is_primary
        }
    }, status=200)

@require_http_methods(['DELETE'])
def portfolio_image_delete(request, slug, image_id):
    """Удалить изображение из галереи"""
    
    item = get_object_or_404(PortfolioItem, slug=slug)
    image = get_object_or_404(PortfolioImage, id=image_id, portfolio_item=item)
    
    if item.seller_id != request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'У вас нет прав для удаления'
        }, status=403)
    
    image_id = image.id
    logger.info(f'Image deleted: {image_id} from portfolio {item.id}')
    image.delete()
    
    return JsonResponse({
        'success': True,
        'message': 'Изображение успешно удалено'
    }, status=200)
