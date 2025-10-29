import pytest
from django.test import Client
from apps.content.models import Channel, ChannelRole
from apps.posts.models import Post
from apps.comments.models import Comment
from apps.memberships.models import ChannelMembership
from unittest.mock import Mock, patch


@pytest.fixture
def api_client():
    """Базовый API клиент для тестов"""
    return Client()


@pytest.fixture
def authenticated_client(api_client, mock_user):
    """API клиент с аутентифицированным пользователем"""
    api_client.force_login(mock_user)
    return api_client


@pytest.fixture
def mock_user():
    """Мок пользователя для тестов"""
    user = Mock()
    user.id = 1
    user.username = 'testuser'
    user.email = 'test@example.com'
    user.is_authenticated = True
    return user


@pytest.fixture
def mock_user_data():
    """Данные пользователя для API ответов"""
    return {
        'id': 1,
        'username': 'testuser',
        'email': 'test@example.com',
        'avatar_url': 'https://example.com/avatar.jpg'
    }


@pytest.fixture
def mock_get_user(mock_user_data):
    """Мок функции get_user из apps.common.api"""
    with patch('apps.common.api.get_user') as mock:
        mock.return_value = mock_user_data
        yield mock


@pytest.fixture
def mock_get_users_batch():
    """Мок функции get_users_batch из apps.common.api"""
    with patch('apps.common.api.get_users_batch') as mock:
        mock.return_value = [
            {
                'id': 1,
                'username': 'testuser',
                'email': 'test@example.com',
                'avatar_url': 'https://example.com/avatar.jpg'
            }
        ]
        yield mock


@pytest.fixture
def mock_verify_user_exists():
    """Мок функции verify_user_exists из apps.common.api"""
    with patch('apps.common.api.verify_user_exists') as mock:
        mock.return_value = True
        yield mock


@pytest.fixture
@pytest.mark.django_db
def channel(mock_user):
    """Создание тестового канала"""
    return Channel.objects.create(
        name='Test Channel',
        slug='test-channel',
        description='Test channel description',
        owner_id=mock_user.id
    )


@pytest.fixture
@pytest.mark.django_db
def post(channel, mock_user):
    """Создание тестового поста"""
    return Post.objects.create(
        channel=channel,
        author_id=mock_user.id,
        title='Test Post',
        slug='test-post',
        content='Test post content',
        image_url='https://example.com/image.jpg'
    )


@pytest.fixture
@pytest.mark.django_db
def comment(post, mock_user):
    """Создание тестового комментария"""
    return Comment.objects.create(
        post=post,
        author_id=mock_user.id,
        content='Test comment content'
    )


@pytest.fixture
@pytest.mark.django_db
def channel_membership(channel, mock_user):
    """Создание тестового членства в канале"""
    return ChannelMembership.objects.create(
        channel=channel,
        user_id=mock_user.id,
        role=ChannelRole.MEMBER
    )


@pytest.fixture
@pytest.mark.django_db
def owner_membership(channel, mock_user):
    """Создание владельца канала"""
    return ChannelMembership.objects.create(
        channel=channel,
        user_id=mock_user.id,
        role=ChannelRole.OWNER
    )


@pytest.fixture
@pytest.mark.django_db
def admin_membership(channel):
    """Создание администратора канала"""
    return ChannelMembership.objects.create(
        channel=channel,
        user_id=2,
        role=ChannelRole.ADMIN
    )


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Автоматически включает доступ к БД для всех тестов
    Можно убрать autouse=True если нужно явно указывать @pytest.mark.django_db
    """
    pass


@pytest.fixture
def sample_channel_data():
    """Данные для создания канала"""
    return {
        'name': 'New Channel',
        'description': 'New channel description'
    }


@pytest.fixture
def sample_post_data():
    """Данные для создания поста"""
    return {
        'title': 'New Post Title',
        'content': 'New post content with enough characters',
        'image_url': 'https://example.com/new-image.jpg'
    }


@pytest.fixture
def sample_comment_data():
    """Данные для создания комментария"""
    return {
        'content': 'New comment content'
    }
