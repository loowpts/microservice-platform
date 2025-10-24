from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from apps.users.models import User, UserProfile
from apps.users.forms import RegisterForm, ProfileForm
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
            return JsonResponse({'error': 'User ID required'}, status=400)
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
        user_id = request.POST.get('user_id')
        if not user_id:
            logger.error("User ID not provided")
            return JsonResponse({'error': 'User ID required'}, status=400)
        user = get_object_or_404(User, id=user_id)
        profile = user.profile
        logger.debug(f"Received data: {request.POST}")
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            logger.info(f"Profile updated for user: {user.email}")
            return JsonResponse({'status': 'profile_updated'}, status=200)
        logger.error(f"Form errors: {form.errors.as_json()}")
        return JsonResponse({'error': form.errors.as_json()}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

def delete_user(request, pk):
    if request.method == 'DELETE':
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
        target_user_id = request.POST.get('user_id')
        try:
            target_user_id = int(target_user_id)
        except ValueError:
            logger.error(f"Invalid user_id: {target_user_id}")
            return JsonResponse({'error': 'Invalid user ID'}, status=400)
        role = request.POST.get('role')
        try:
            target_user = User.objects.get(id=target_user_id)
            if role == 'freelancer':
                target_user.is_freelancer = True
            elif role == 'seller':
                target_user.is_seller = True
            elif role == 'moderator':
                target_user.is_moderator = True
            else:
                logger.error(f"Invalid role: {role}")
                return JsonResponse({'error': 'Invalid role'}, status=400)
            target_user.save()
            logger.info(f"Role {role} set for user: {target_user.email}")
            return JsonResponse({'status': 'role_updated'}, status=200)
        except User.DoesNotExist:
            logger.error(f"User ID {target_user_id} not found")
            return JsonResponse({'error': 'User not found'}, status=404)
    return JsonResponse({'error': 'Method not allowed'}, status=405)
