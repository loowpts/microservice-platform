import pytest
from django.urls import reverse
from django.test import Client
from apps.users.models import User, UserProfile

@pytest.fixture
def client():
    return Client()

@pytest.fixture
def user():
    return User.objects.create_user(
        email='test@test.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )

@pytest.fixture
def admin():
    return User.objects.create_superuser(
        email='admin@test.com',
        password='adminpass123'
    )

@pytest.mark.django_db
def test_create_user(client):
    response = client.post(reverse('users:create_user'), {
        'email': 'new@test.com',
        'password1': 'testpass123',
        'password2': 'testpass123',
        'first_name': 'New',
        'last_name': 'User'
    })
    assert response.status_code == 201
    assert response.json()['status'] == 'success'
    assert User.objects.filter(email='new@test.com').exists()
    assert response.json()['user']['email'] == 'new@test.com'

@pytest.mark.django_db
def test_create_user_invalid(client):
    response = client.post(reverse('users:create_user'), {
        'email': 'invalid',  # Неверный email
        'password1': 'testpass123',
        'password2': 'testpass123'
    })
    assert response.status_code == 400
    assert 'error' in response.json()

@pytest.mark.django_db
def test_get_profile(client, user):
    response = client.get(reverse('users:profile'), {'user_id': user.id})
    assert response.status_code == 200
    assert response.json()['profile']['email'] == user.email
    assert response.json()['profile']['role_display'] == 'User'

@pytest.mark.django_db
def test_get_profile_missing_user_id(client):
    response = client.get(reverse('users:profile'))
    assert response.status_code == 400
    assert response.json()['error'] == 'User ID required'

@pytest.mark.django_db
def test_get_profile_detail_public(client, user):
    response = client.get(reverse('users:profile_detail', kwargs={'pk': user.pk}))
    assert response.status_code == 200
    assert response.json()['profile']['email'] == user.email
    assert response.json()['profile']['is_public'] is True

@pytest.mark.django_db
def test_get_profile_detail_private(client, user):
    user.profile.is_public = False
    user.profile.save()
    response = client.get(reverse('users:profile_detail', kwargs={'pk': user.pk}))
    assert response.status_code == 403
    assert response.json()['error'] == 'Profile is private'

@pytest.mark.django_db
def test_update_profile(client, user):
    response = client.put(
        reverse('users:update_profile'),
        data={
            'bio': 'Updated bio',
            'is_public': 'true',
            'timezone': 'UTC',
            'streak_visibility': 'true',
            'user_id': str(user.id)
        },
        content_type='application/x-www-form-urlencoded'
    )
    assert response.status_code == 200, f"Failed with response: {response.content}"
    assert response.json()['status'] == 'profile_updated'
    user.profile.refresh_from_db()
    assert user.profile.bio == 'Updated bio'

@pytest.mark.django_db
def test_update_profile_invalid(client, user):
    response = client.put(
        reverse('users:update_profile'),
        data={
            'bio': 'x' * 1001,
            'user_id': str(user.id)
        },
        content_type='application/x-www-form-urlencoded'
    )
    assert response.status_code == 400
    assert 'error' in response.json()

@pytest.mark.django_db
def test_set_role_admin(client, user, admin):
    response = client.post(
        reverse('users:set_role'),
        data={
            'user_id': str(user.id),
            'role': 'freelancer',
            'admin_id': str(admin.id)
        },
        content_type='application/x-www-form-urlencoded'
    )
    assert response.status_code == 200, f"Failed with response: {response.content}"
    assert response.json()['status'] == 'role_updated'
    user.refresh_from_db()
    assert user.is_freelancer is True

@pytest.mark.django_db
def test_set_role_non_admin(client, user):
    response = client.post(
        reverse('users:set_role'),
        data={
            'user_id': str(user.id),
            'role': 'freelancer',
            'admin_id': str(user.id)
        },
        content_type='application/x-www-form-urlencoded'
    )
    assert response.status_code == 403, f"Failed with response: {response.content}"
    assert response.json()['error'] == 'Forbidden'
