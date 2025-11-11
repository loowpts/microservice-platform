import json
import logging
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.db.models import Q


from .models import Product, ProductImage
from apps.categories.models import Category
from apps.common.api import get_user, get_users_batch
from .forms import ProductForm


logger = logging.getLogger(__name__)

@require_http_methods(['GET'])
def product_list(request):
    products = Product.objects.filter(status='active')

    category = request.GET.get('category')
    city = request.GET.get('city')
    condition = request.GET.get('condition')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    status = request.GET.get('status')
    seller_id = request.GET.get('seller_id')

    try:
        price_min = float(price_min) if price_min else None
    except ValueError:
        price_min = None

    try:
        price_max = float(price_max) if price_max else None
    except ValueError:
        price_max = None

    try:
        seller_id = int(seller_id) if seller_id else None
    except ValueError:
        seller_id = None

    if category:
        products = products.filter(category__slug=category)
    if city:
        products = products.filter(city__icontains=city)
    if condition:
        products = products.filter(condition=condition)
    if status:
        products = products.filter(status=status)
    if price_min is not None:
        products = products.filter(price__gte=price_min)
    if price_max is not None:
        products = products.filter(price__lte=price_max)
    if seller_id:
        products = products.filter(seller_id=seller_id)

    products = products.select_related('category').prefetch_related('additional_images').order_by('-created_at')

    seller_ids = list(products.values_list('seller_id', flat=True).distinct())
    sellers_data = get_users_batch(seller_ids)
    seller_maps = {u['id']: u for u in sellers_data}

    data = []

    for product in products:
        user_data = seller_maps.get(product.seller_id)
        image = product.additional_images.filter(is_primary=True).first() or product.additional_images.first()

        data.append({
            'id': product.id,
            'title': product.title,
            'slug': product.slug,
            'price': product.price,
            'old_price': product.old_price,
            'category': {
                'id': product.category.id if product.category else None,
                'name': product.category.name if product.category else None,
                'slug': product.category.slug if product.category else None,
            } if product.category else None,
            'condition': product.condition,
            'city': product.city,
            'status': product.status,
            'seller_id': product.seller_id,
            'seller': {
                'id': user_data['id'],
                'email': user_data.get('email', ''),
                'avatar_url': user_data.get('avatar_url')
            } if user_data else None,
            'image_url': image.image_url if image else None,
            'views_count': product.views_count,
            'created_at': product.created_at.isoformat()
        })

    return JsonResponse({
        'success': True,
        'count': len(data),
        'data': data
    }, status=200)
    
@require_http_methods(['GET'])
def product_detail(request, slug):
    
    product = get_object_or_404(
        Product,
        slug=slug
    )

    product.views_count = (product.views_count or 0) + 1
    product.save(update_fields=["views_count"])
    
    images = product.additional_images.all()
    
    seller = get_user(product.seller_id)

    images_data = [
        {
            'id': img.id,
            'image_url': img.image_url,
            'is_primary': img.is_primary,
            'order': img.order,
        }
        for img in images
    ]
    
    data = {
        "id": product.id,
        "title": product.title,
        "slug": product.slug,
        "description": product.description,
        "price": product.price,
        "old_price": product.old_price,
        "category": {
            "id": product.category.id if product.category else None,
            "name": product.category.name if product.category else None,
            "slug": product.category.slug if product.category else None,
        } if product.category else None,
        "condition": product.condition,
        "status": product.status,
        "city": product.city,
        "quantity": product.quantity,
        "views_count": product.views_count,
        "seller_id": product.seller_id,
        "seller": seller,
        "images": images_data,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
    }
    
    logger.info(f'Product viewed: {product.id}')
    
    return JsonResponse({
        'success': True,
        'data': data
    }, status=200)


@require_http_methods(['POST'])
def product_create(request):
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Невалидный Json'
        }, status=400)
    
    form = ProductForm(data)
    
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)
    
    product = form.save(commit=False)
    product.seller_id = request.user.id
    product.status = 'draft'
    
    main_image_url = data.get('main_image')
    if main_image_url:
        product.main_image = main_image_url
        
    product.save()
    
    images_urls = data.get('images', [])
    if isinstance(images_urls, list):
        for i, url in enumerate(images_urls):
            ProductImage.objects.create(
                product=product,
                image_url=url,
                order=i
            )
        
    seller_data = get_user(product.seller_id)

    response_data = {
        'id': product.id,
        'title': product.title,
        'slug': product.slug,
        'description': product.description,
        'price': product.price,
        'old_price': product.old_price,
        'category': {
            'id': product.category.id if product.category else None,
            'name': product.category.name if product.category else None,
            'slug': product.category.slug if product.category else None,
        } if product.category else None,
        'condition': product.condition,
        'status': product.status,
        'city': product.city,
        'quantity': product.quantity,
        'views_count': product.views_count,
        'seller_id': product.seller_id,
        'seller': seller_data,
        'main_image': product.main_image,
        'created_at': product.created_at.isoformat(),
        'updated_at': product.updated_at.isoformat(),
    }
    
    logger.info(f'Product created: {product.id} by user {request.user.id}')
    
    return JsonResponse({
        'success': True,
        'message': 'Товар успешно создан и находится на модерации.',
        'data': response_data
    }, status=201)
            
@require_http_methods(['PATCH'])
def product_update(request, slug):
    product = get_object_or_404(
        Product,
        slug=slug,
    )
    
    if product.seller_id != request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'Вы не можете редактировать чужой продукт!',
            'code': 'permission_denied'
        }, status=403)
        
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Невалидный Json'
        }, status=400)
    
    form = ProductForm(data, instance=product)

    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)
    
    form.save()
    
    images_urls = data.get('images')
    if isinstance(images_urls, list):
        ProductImage.objects.filter(product=product).delete()
        
        for i, url in enumerate(images_urls):
            ProductImage.objects.create(
                product=product,
                image_url=url,
                order=i
            )
            
    seller_data = get_user(product.seller_id)
    
    response_data = {
        'id': product.id,
        'title': product.title,
        'slug': product.slug,
        'description': product.description,
        'price': product.price,
        'old_price': product.old_price,
        'category': {
            'id': product.category.id if product.category else None,
            'name': product.category.name if product.category else None,
            'slug': product.category.slug if product.category else None,
        } if product.category else None,
        'condition': product.condition,
        'status': product.status,
        'city': product.city,
        'quantity': product.quantity,
        'views_count': product.views_count,
        'seller_id': product.seller_id,
        'seller': seller_data,
        'main_image': product.main_image,
        'created_at': product.created_at.isoformat(),
        'updated_at': product.updated_at.isoformat(),
    }

    logger.info(f'Product updated: {product.id} by user {request.user.id}')
    
    return JsonResponse({
        'success': True,
        'message': 'Товар обновлен',
        'data': response_data
    }, status=200)


@require_http_methods(['DELETE'])
def product_delete(request, slug):
    product = get_object_or_404(
        Product,
        slug=slug
    )
    
    if product.seller_id != request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'Вы не можете удалить чужой товар.',
            'code': 'permission_denied'
            
        }, status=403)

    product_id = product.id
    
    product.delete()
    
    logger.info(f'Product deleted: {product_id} by user {request.user.id}')
    
    return JsonResponse({
        'success': True,
        'message': 'Товар удален'
    }, status=200)
    
@require_http_methods(['GET'])
def my_products(request):
    
    products = Product.objects.filter(seller_id=request.user.id).order_by('-created_at')
    
    status = request.GET.get('status')
    
    if status:
        products = products.filter(status=status)
        
    products = products.select_related('category').prefetch_related('additional_images').order_by('-created_at')
    
    data = []
    
    for product in products:
        image = product.additional_images.filter(is_primary=True).first() or product.additional_images.first()
        data.append({
            'id': product.id,
            'title': product.title,
            'slug': product.slug,
            'price': product.price,
            'old_price': product.old_price,
            'category': {
                'id': product.category.id if product.category else None,
                'name': product.category.name if product.category.name else None,
                'slug': product.category.slug if product.category.slug else None,
            } if product.category else None,
            'condition': product.condition,
            'city': product.city,
            'status': product.status,
            'seller_id': product.seller_id,
            'image_url': image.image_url if image else None,
            'views_count': product.views_count,
            'created_at': product.created_at.isoformat(),
        })
    
    return JsonResponse({
        'success': True,
        'count': products.count(),
        'data': data
    }, status=200)
