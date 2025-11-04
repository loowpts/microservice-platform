import json
import logging
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from .models import Category


@require_http_methods(['GET'])
def category_list(request):
    categories = Category.objects.all().order_by('order', 'name')
    
    data = []
    for category in categories:
        data.append({
            'id': category.id,
            'name': category.name,
            'slug': category.slug,
            'icon': category.icon if category.icon else None,
            'parent_id': category.parent.id if category.parent else None,
            'subcategories_count': category.subcategories.count()
        })
    
    return JsonResponse({
        'success': True,
        'count': categories.count(),
        'data': data
    }, status=200)
    
@require_http_methods(['GET'])
def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    
    subcategories = category.subcategories.all().order_by('order')
    
    subcategories_data = []
    for subcategorie in subcategories:
        subcategories_data.append({
            'id': subcategorie.id,
            'name': subcategorie.name,
            'slug': subcategorie.slug,
            'icon': subcategorie.icon if subcategorie.icon else None
        })
    
    data = {
        'id': category.id,
        'name': category.name,
        'slug': category.slug,
        'icon': category.icon if category.icon else None,
        'parent': {
            'id': category.parent.id,
            'name': category.parent.name,
            'slug': category.parent.slug
        } if category.parent else None,
        'subcategories_count': subcategories.count(),
        'subcategories_data': subcategories_data
    }
    
    return JsonResponse({
        'success': True,
        'data': data
    }, status=200)
    
    
    
    
    
    
