import json
import urllib.parse
import logging
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from apps.users.models import User, UserProfile
from apps.users.forms import RegisterForm, ProfileForm
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from apps.common.notifications import send_notification
from django.contrib.auth.decorators import login_required
from apps.common.decorators import (
    staff_required,
    owner_or_staff_required,
    public_endpoint
)

logger = logging.getLogger(__name__)

def health_check(request):
    """Health check endpoint"""
    return JsonResponse({'status': 'healthy', 'service': 'user-service'})

@csrf_exempt
@public_endpoint
def create_user(request):
    """
    Публичный эндпоинт для регистрации пользователей
    POST /api/users/
    """
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_notification(
                user_id=user.id,
                event='user_registered',
                title='Добро пожаловать!',
                message=f'Здравствуйте, {user.first_name}! Ваш аккаунт успешно создан.',
                notification_type='in_app'
            )
            logger.info(f"User created: {user.email}")
            return JsonResponse({
                'status': 'success',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role_display': user.profile.role_display()
                }
            }, status=201)
        logger.error(f"Form errors: {form.errors.as_json()}")
        return JsonResponse({'error': form.errors.as_json()}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@owner_or_staff_required
def get_profile(request):
    """
    Получить профиль пользователя (владелец или staff)
    GET /api/profile/?user_id=X
    """
    if request.method == 'GET':
        user_id = request.GET.get('user_id')
        if not user_id:
            logger.error("User ID not provided")
            return JsonResponse({'error': 'User ID required'}, status=400)
        try:
            user_id = int(user_id)
        except ValueError:
            logger.error(f"Invalid user_id: {user_id}")
            return JsonResponse({'error': 'Invalid user ID'}, status=400)
        
        user = get_object_or_404(User, id=user_id)
        profile = user.profile
        
        return JsonResponse({
            'profile': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'bio': profile.bio,
                'avatar': profile.avatar.url if profile.avatar else None,
                'is_public': profile.is_public,
                'timezone': profile.timezone,
                'streak_visibility': profile.streak_visibility,
                'role_display': profile.role_display(),
                'is_freelancer': user.is_freelancer,
                'is_seller': user.is_seller,
                'is_moderator': user.is_moderator,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser
            }
        }, status=200)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
@public_endpoint
def get_profile_detail(request, pk):
    """
    Публичный просмотр профиля (только если is_public=True)
    GET /api/profile/<pk>/
    """
    if request.method == 'GET':
        profile = get_object_or_404(UserProfile.objects.select_related('user'), user__pk=pk)
        
        if not profile.is_public:
            # Если профиль приватный, проверяем аутентификацию
            if not getattr(request, 'authenticated', False):
                return JsonResponse({'error': 'Profile is private'}, status=403)
            
            # Если это не владелец и не staff - запрещаем
            user = request.user
            if user.id != pk and not (user.is_staff or user.is_superuser):
                return JsonResponse({'error': 'Profile is private'}, status=403)
        
        return JsonResponse({
            'profile': {
                'id': profile.user.id,
                'email': profile.user.email,
                'first_name': profile.user.first_name,
                'last_name': profile.user.last_name,
                'bio': profile.bio,
                'avatar': profile.avatar.url if profile.avatar else None,
                'is_public': profile.is_public,
                'role_display': profile.role_display(),
                'is_freelancer': profile.user.is_freelancer,
                'is_seller': profile.user.is_seller,
                'is_moderator': profile.user.is_moderator
            }
        }, status=200)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@owner_or_staff_required
def update_profile(request):
    """
    Обновить профиль (владелец или staff)
    PUT /api/profile/update/
    """
    if request.method == 'PUT':
        data = request.POST
        logger.debug(f"Received PUT data (POST): {data}")
        
        if not data:
            try:
                raw_data = request.body.decode('utf-8')
                data = urllib.parse.parse_qs(raw_data)
                data = {k: v[0] for k, v in data.items() if v}
                logger.debug(f"Parsed body data: {data}")
            except Exception as e:
                logger.error(f"Failed to parse request.body: {e}")
                return JsonResponse({'error': 'Invalid data format'}, status=400)

        user_id = data.get('user_id')
        if not user_id:
            logger.error("User ID not provided")
            return JsonResponse({'error': 'User ID required'}, status=400)
        
        try:
            user_id = int(user_id)
        except ValueError:
            logger.error(f"Invalid user_id: {user_id}")
            return JsonResponse({'error': 'Invalid user ID'}, status=400)
        
        user = get_object_or_404(User, id=user_id)
        profile = user.profile
        form = ProfileForm(data, request.FILES, instance=profile)
        
        if form.is_valid():
            form.save()
            logger.info(f"Profile updated for user: {user.email}")
            return JsonResponse({'status': 'profile_updated'}, status=200)
        
        logger.error(f"Form errors: {form.errors.as_json()}")
        return JsonResponse({'error': form.errors.as_json()}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@staff_required
def delete_user(request, pk):
    """
    Удалить пользователя (только staff)
    DELETE /api/users/<pk>/delete/
    """
    if request.method == 'DELETE':
        try:
            pk = int(pk)
        except ValueError:
            logger.error(f"Invalid pk: {pk}")
            return JsonResponse({'error': 'Invalid user ID'}, status=400)
        
        user = get_object_or_404(User, id=pk)
        user_email = user.email
        user.delete()
        
        logger.info(f"User deleted: {user_email}")
        return JsonResponse({}, status=204)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@staff_required
def set_role(request):
    """
    Установить роль пользователя (только staff)
    POST /api/set-role/
    """
    if request.method == 'POST':
        logger.debug(f"Received POST data: {request.POST}")
        
        # admin_id больше не нужен - берем из request.user
        admin = request.user
        
        user_id = request.POST.get('user_id')
        role = request.POST.get('role')
        
        if not user_id or not role:
            logger.error(f"Missing user_id or role: user_id={user_id}, role={role}")
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        try:
            user_id = int(user_id)
        except ValueError:
            logger.error(f"Invalid user_id: {user_id}")
            return JsonResponse({'error': 'Invalid user ID'}, status=400)
        
        user = get_object_or_404(User, id=user_id)
        
        if role not in ['freelancer', 'seller', 'moderator']:
            logger.error(f"Invalid role: {role}")
            return JsonResponse({'error': 'Invalid role'}, status=400)
        
        # Сбрасываем все роли
        user.is_freelancer = user.is_seller = user.is_moderator = False
        # Устанавливаем новую роль
        setattr(user, f'is_{role}', True)
        user.save()
        
        logger.info(f"Role {role} set for user: {user.email} by {admin.email}")
        return JsonResponse({'status': 'role_updated'}, status=200)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
@public_endpoint
@require_http_methods(['POST'])
def login(request):
    """
    Публичный эндпоинт для входа
    POST /api/auth/login/
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    
    # Поддержка как email, так и username
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    # Используем email или username (что было передано)
    login_field = email or username

    if not login_field or not password:
        return JsonResponse({
            'success': False,
            'error': 'Все поля обязательны для заполнения.'
        }, status=400)

    login_field = login_field.lower().strip()
    user = authenticate(request, username=login_field, password=password)
    
    if user is None:
        logger.warning(f"Failed login attempt for email: {email}")
        return JsonResponse({
            'success': False,
            'error': 'Invalid credentials'
        }, status=401)
    
    if not user.is_active:
        logger.warning(f"Login attempt for disabled account: {email}")
        return JsonResponse({
            'success': False,
            'error': 'Account is disabled'
        }, status=403)
    
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)

    logger.info(f"User logged in: {user.email}")
    
    return JsonResponse({
        'status': 'success',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role_display': user.profile.role_display()
        }
    }, status=200)


@login_required
@require_http_methods(['POST'])
def logout(request):
    """
    Выход (требует аутентификации)
    POST /api/auth/logout/
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    
    refresh_token = data.get('refresh_token')
    if not refresh_token:
        return JsonResponse({
            'success': False,
            'error': 'refresh_token is required'
        }, status=400)
    
    try:
        token = RefreshToken(refresh_token)
        
        try:
            token.blacklist()
            logger.info(f'User {request.user.email} logged out (token blacklisted)')
        except AttributeError:
            logger.info(f'User {request.user.email} logged out (blacklist not configured)')
        
        return JsonResponse({
            'status': 'success',
            'message': 'Logged out successfully'
        }, status=200)
        
    except TokenError as e:
        logger.error(f"Invalid refresh token: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Invalid or expired refresh token'
        }, status=400)


@csrf_exempt
@public_endpoint
@require_http_methods(['POST'])
def refresh_token(request):
    """
    Обновить access token (публичный)
    POST /api/auth/refresh/
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    
    refresh_token = data.get('refresh_token')
    
    try:
        token = RefreshToken(refresh_token)
        new_access = str(token.access_token)
        logger.info('Token refreshed successfully')
        return JsonResponse({
            'success': True,
            'access_token': new_access
        }, status=200)
    except TokenError as e:
        logger.error(f"Invalid refresh token: {str(e)}")
        return JsonResponse({'error': 'Invalid or expired refresh token'}, status=400)
    except Exception as e:
        logger.error(f"Error during refresh: {str(e)}")
        return JsonResponse({'error': 'Refresh failed'}, status=500)


@login_required
@require_http_methods(['POST'])
def verify_token(request):
    """
    Проверить валидность токена (требует аутентификации)
    POST /api/auth/verify/
    
    Можно также использовать middleware - если request.authenticated = True,
    значит токен валиден
    """
    user = request.user
    
    return JsonResponse({
        'success': True,
        'message': 'Valid',
        'user': {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role_display': user.profile.role_display(),
            'is_freelancer': user.is_freelancer,
            'is_seller': user.is_seller,
            'is_moderator': user.is_moderator,
        }
    }, status=200)


@login_required
@require_http_methods(['POST'])
def get_users_batch(request):
    """
    Получить информацию о нескольких пользователях (требует аутентификации)
    POST /api/users/batch/
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    
    user_ids = data.get('user_ids', [])
    if not isinstance(user_ids, list):
        return JsonResponse({'error': 'user_ids must be a list'}, status=400)

    if not user_ids:
        return JsonResponse({
            'success': False,
            'count': 0,
            'users': []
        }, status=200)
    
    users = User.objects.filter(id__in=user_ids).select_related('profile')
    
    users_data = [
        {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role_display': user.profile.role_display(),
            'is_freelancer': user.is_freelancer,
            'is_seller': user.is_seller,
            'is_moderator': user.is_moderator,
        }
        for user in users
    ]
    
    logger.info(f'Batch request for {len(user_ids)} users by {request.user.email}, found {len(users_data)}')
    
    return JsonResponse({
        'status': 'success',
        'count': len(users_data),
        'users': users_data
    }, status=200)


@login_required
def get_current_user(request):
    """
    Получить информацию о текущем аутентифицированном пользователе
    GET /api/auth/me/
    """
    if request.method == 'GET':
        user = request.user
        profile = user.profile
        
        return JsonResponse({
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'bio': profile.bio,
                'avatar': profile.avatar.url if profile.avatar else None,
                'is_public': profile.is_public,
                'timezone': profile.timezone,
                'streak_visibility': profile.streak_visibility,
                'role_display': profile.role_display(),
                'is_freelancer': user.is_freelancer,
                'is_seller': user.is_seller,
                'is_moderator': user.is_moderator,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'is_active': user.is_active,
                'is_verified': user.is_verified,
                'date_joined': user.date_joined.isoformat(),
            }
        }, status=200)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)
