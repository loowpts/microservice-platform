from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from apps.users.models import User, UserProfile
from apps.users.forms import RegisterForm, ProfileForm
import urllib.parse
import logging

logger = logging.getLogger(__name__)

def create_user(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
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

def get_profile(request):
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

def get_profile_detail(request, pk):
    if request.method == 'GET':
        profile = get_object_or_404(UserProfile.objects.select_related('user'), user__pk=pk)
        if not profile.is_public:
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

def update_profile(request):
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

def delete_user(request, pk):
    if request.method == 'DELETE':
        try:
            pk = int(pk)
        except ValueError:
            logger.error(f"Invalid pk: {pk}")
            return JsonResponse({'error': 'Invalid user ID'}, status=400)
        user = get_object_or_404(User, id=pk)
        user.delete()
        logger.info(f"User deleted: {user.email}")
        return JsonResponse({}, status=204)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

def set_role(request):
    if request.method == 'POST':
        logger.debug(f"Received POST data: {request.POST}")
        admin_id = request.POST.get('admin_id')
        if not admin_id:
            logger.error("Admin ID not provided")
            return JsonResponse({'error': 'Admin ID required'}, status=400)
        try:
            admin_id = int(admin_id)
        except ValueError:
            logger.error(f"Invalid admin_id: {admin_id}")
            return JsonResponse({'error': 'Invalid admin ID'}, status=400)
        admin = get_object_or_404(User, id=admin_id)
        if not admin.is_staff and not admin.is_superuser:
            logger.error(f"User {admin.email} is not staff or superuser")
            return JsonResponse({'error': 'Forbidden'}, status=403)
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
        user.is_freelancer = user.is_seller = user.is_moderator = False
        setattr(user, f'is_{role}', True)
        user.save()
        logger.info(f"Role {role} set for user: {user.email}")
        return JsonResponse({'status': 'role_updated'}, status=200)
    return JsonResponse({'error': 'Method not allowed'}, status=405)
