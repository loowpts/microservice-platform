import json
import logging
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from apps.common.api import get_user, get_users_batch
from apps.posts.models import Post
from .models import Comment
from .forms import CommentForm, CommentReplyForm

logger = logging.getLogger(__name__)


@require_http_methods(['POST'])
def comment_create(request, post_slug, channel_slug):
    
    post = get_object_or_404(
        Post,
        slug=post_slug,
        channel__slug=channel_slug
    )
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Невалидный Json'
        }, status=400)
    
    form = CommentForm(data)
    
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)
    
    comment = form.save(commit=False)
    comment.post = post
    comment.author_id = request.user.id
    comment.save()
    
    author_data = get_user(request.user.id)
    
    response_data = {
        'id': comment.id,
        'content': comment.content,
        'author_id': comment.author_id,
        'author': {
            'id': author_data['id'],
            'email': author_data.get('email', ''),
            'avatar_url': author_data.get('avatar_url')
        } if author_data else None,
        'replies_count': 0,
        'created_at': comment.created_at.isoformat()
    }
    
    logger.info(f'Comment created: {comment.id} on post {post.id} by user {request.user.id}')
    
    return JsonResponse({
        'success': True,
        'message': 'Комментарий успешно добавлен',
        'data': response_data
        
    }, status=201)
    
@require_http_methods(['PATCH'])
def comment_update(request, comment_id, post_slug, channel_slug):
    
    comment = get_object_or_404(
        Comment,
        id=comment_id,
        post__slug=post_slug,
        post__channel__slug=channel_slug
    )
    
    if comment.author_id != request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'Вы можете редактировать только свои комментарии',
            'code': 'permission_denied'
        }, status=403)
        
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Невалидный Json'
        }, status=400)
    
    form = CommentForm(data, instance=comment)
    
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'error': form.errors
        }, status=400)
    
    form.save()
    
    response_data = {
        'id': comment.id,
        'content': comment.content,
        'created_at': comment.created_at.isoformat()
    }
    
    logger.info(f'Comment updated: {comment.id} by user {request.user.id}')
    
    return JsonResponse({
        'success': True,
        'message': 'Комментарий обновлен.',
        'data': response_data
    }, status=200)

@require_http_methods(['DELETE'])
def comment_delete(request, comment_id, post_slug, channel_slug):
    
    comment = get_object_or_404(
        Comment,
        id=comment_id,
        post__slug=post_slug,
        post__channel__slug=channel_slug
    )
    
    if comment.author_id != request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'Вы можете удалять только свои комментарии',
            'code': 'permission_denied'
            
        }, status=403)

    comment_id = comment.id
    comment.delete()
    
    logger.info(f'Comment: {comment_id} deleted by user - {request.user.id}')
    
    return JsonResponse({
        'success': True,
        'message': 'Комментарий удален'
    }, status=200)
    
@require_http_methods(['POST'])
def comment_reply(request, comment_id, post_slug, channel_slug):
    
    parent_comment = get_object_or_404(
        Comment,
        id=comment_id,
        post__slug=post_slug,
        post__channel__slug=channel_slug
    )
    
    if parent_comment.parent is not None:
        return JsonResponse({
            'success': False,
            'error': 'Нельзя отвечать на ответ',
            'code': 'invalid_parent'
        }, status=400)
        
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Невалидный Json'
        }, status=400)
        
    data['parent'] = parent_comment.id
    
    form = CommentReplyForm(data)
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)
    
    reply = form.save(commit=False)
    reply.post = parent_comment.post
    reply.author_id = request.user.id
    reply.save()
    
    author_data = get_user(request.user.id)
    
    response_data = {
        'id': reply.id,
        'content': reply.content,
        'author_id': reply.author_id,
        'author': {
            'id': author_data['id'],
            'email': author_data.get('email', ''),
            'avatar_url': author_data.get('avatar_url')
        } if author_data else None,
        'parent_id': parent_comment.id,
        'created_at': reply.created_at.isoformat()
    }
    
    logger.info(f'Reply created: {reply.id} on comment {parent_comment.id} by user {request.user.id}')

    return JsonResponse({
        'success': True,
        'message': 'Ответ добавлен',
        'data': response_data
    }, status=201)
    
@require_http_methods(['GET'])
def comment_list(request, post_slug, channel_slug):
    post = get_object_or_404(
        Post,
        slug=post_slug,
        channel__slug=channel_slug
    )
    
    comments = Comment.objects.filter(
        post=post,
        parent=None
    ).order_by('-created_at')
    
    author_ids = set()
    
    for comment in comments:
        author_ids.add(comment.author_id)
    
        for reply in comment.replies.all():
            author_ids.add(reply.author_id)
    
    users_data = get_users_batch(list(author_ids))
    users_map = {u['id']: u for u in users_data}
    
    data = []

    for comment in comments:
        author_data = users_map.get(comment.author_id)
        
        replies_data = []
        for reply in comment.replies.all().order_by('created_at'):
            reply_author = users_map.get(reply.author_id)
            
            replies_data.append({
                'id': reply.id,
                'content': reply.content,
                'author_id': reply.author_id,
                'author': {
                    'id': reply_author['id'],
                    'email': reply_author.get('email', ''),
                    'avatar_url': reply_author.get('avatar_url')
                } if reply_author else None,
                'created_at': reply.created_at.isoformat()
            })
        
        data.append({
            'id': comment.id,
            'content': comment.content,
            'author_id': comment.author_id,
            'author': {
                'id': author_data['id'],
                'email': author_data.get('email', ''),
                'avatar_url': author_data.get('avatar_url')
            } if author_data else None,
            'replies_count': comment.replies.count(),
            'replies': replies_data,
            'created_at': comment.created_at.isoformat()
        })
        
    return JsonResponse({
        'success': True,
        'post': {
            'id': post.id,
            'title': post.title,
            'slug': post.slug
        },
        'count': len(data),
        'data': data
    }, status=200)
    
