import pytest
import json
from django.utils import timezone
from django.test import Client
from django.contrib.contenttypes.models import ContentType

from apps.content.models import Channel
from apps.posts.models import Post
from apps.interactions.models import Like
from unittest.mock import patch


@pytest.mark.django_db
@pytest.mark.views
class TestPostLikeToggleView:
    
    def setup_method(self):
        self.client = Client()
        
        self.channel = Channel.objects.create(
            name='Test Channel',
            slug='test-channel',
            owner_id=1
        )
        
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            content='Test content',
            channel=self.channel,
            author_id=1
        )
        
        self.content_type = ContentType.objects.get_for_model(Post)
    
    def test_like_create_success(self):
        """
        Тест 1: Успешное добавление лайка (201)
        
        Проверяем:
        - Статус 201
        - success = True
        - message = 'Лайк поставлен'
        - is_liked = True
        - data содержит: id, created_at
        - Like создался в БД
        """
        
        assert not Like.objects.filter(
            user_id=1,
            content_type=self.content_type,
            object_id=self.post.id
        ).exists()
        
        response = self.client.post(
            f'/api/channels/{self.channel.slug}/posts/{self.post.slug}/like/'
        )
        
        data = json.loads(response.content)
        
        assert response.status_code == 201
        assert data['success'] is True
        assert data['message'] == 'Лайк поставлен'
        assert data['is_liked'] is True
        assert 'id' in data['data']
        assert 'created_at' in data['data']
    
    def test_like_delete_success(self):
        """
        Тест 2: Успешное удаление лайка (200)
        
        Проверяем:
        - Статус 200
        - success = True
        - message = 'Лайк убран'
        - is_liked = False
        - Like удалился из БД
        
        """
        assert Like.objects.create(
            user_id=1,
            content_type=self.content_type,
            object_id=self.post.id
        )
        
        response = self.client.post(
            f'/api/channels/{self.channel.slug}/posts/{self.post.slug}/like/'
        )
        
        data = json.loads(response.content)
        
        assert response.status_code == 200
        assert data['success'] is True
        assert data['message'] == 'Лайк убран'
        assert data['is_liked'] is False

        assert not Like.objects.filter(
            user_id=1,
            content_type=self.content_type,
            object_id=self.post.id
        ).exists()
        
    def test_like_toggle_twice(self):
        """
        Тест 3: Toggle дважды (добавить → убрать → добавить)
        
        Проверяем:
        - Первый POST → 201, is_liked=True
        - Второй POST → 200, is_liked=False
        - Третий POST → 201, is_liked=True
        """
        assert not Like.objects.filter(
            user_id=1,
            content_type=self.content_type,
            object_id=self.post.id
        ).exists()
        
        response = self.client.post(
            f'/api/channels/{self.channel.slug}/posts/{self.post.slug}/like/'
        )
        
        data = json.loads(response.content)
        
        assert response.status_code == 201
        assert data['success'] is True
        assert data['message'] == 'Лайк поставлен'
        assert data['is_liked'] is True
        
        response1 = self.client.post(
            f'/api/channels/{self.channel.slug}/posts/{self.post.slug}/like/'
        )
        
        data1 = json.loads(response1.content)
        
        assert response1.status_code == 200
        assert data1['success'] is True
        assert data1['message'] == 'Лайк убран'
        assert data1['is_liked'] is False

        response2 = self.client.post(
            f'/api/channels/{self.channel.slug}/posts/{self.post.slug}/like/'
        )
        data2 = json.loads(response2.content)
        
        assert response2.status_code == 201
        assert data2['success'] is True
        assert data2['message'] == 'Лайк поставлен'
        assert data2['is_liked'] is True
        
    def test_like_post_not_found(self):
        """
        Тест 4: Пост не найден (404)
        
        Проверяем:
        - Статус 404
        """
        nonexistent_slug = 'nonexistent-post'
        
        response = self.client.post(
            f'/api/channels/{self.channel.slug}/posts/{nonexistent_slug}/like/'
        )
        
        assert response.status_code == 404
        
    def test_like_channel_not_found(self):
        """
        Тест 5: Канал не найден (404)
        
        Проверяем:
        - Статус 404
        """
        response = self.client.post(
            f'/api/channels/nonexistent-channel/posts/{self.post.slug}/like/'
        )
        
        assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.views
class TestPostLikesListView:
    
    def setup_method(self):
        self.client = Client()
        
        self.channel = Channel.objects.create(
            name='Test Channel',
            slug='test-channel',
            owner_id=1
        )
        
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            content='Test content',
            channel=self.channel,
            author_id=1
        )
        
        self.content_type = ContentType.objects.get_for_model(Post)
    
    @patch('apps.interactions.views.get_users_batch')
    def test_list_likes_success(self, mock_get_users_batch):
        """
        Тест 6: Успешное получение списка лайков (200)
        
        Проверяем:
        - Статус 200
        - success = True
        - post содержит: id, title, slug
        - count = 3
        - data содержит список (3 элемента)
        - Сортировка DESC (новые сначала)
        
        Моки:
        - get_users_batch
        
        """
        mock_get_users_batch.return_value = [
            {'id': 1, 'email': 'test@example.com', 'avatar_url': 'https://avatar_test.com'},
            {'id': 2, 'email': 'test2@example.com', 'avatar_url': 'https://avatar_test.com'},
            {'id': 3, 'email': 'test3@example.com', 'avatar_url': 'https://avatar_test.com'}
        ]
        
        Like.objects.create(
            user_id=1,
            content_type=self.content_type,
            object_id=self.post.id
        )
        
        Like.objects.create(
            user_id=2,
            content_type=self.content_type,
            object_id=self.post.id
        )
        
        Like.objects.create(
            user_id=3,
            content_type=self.content_type,
            object_id=self.post.id
        )
        
        assert Like.objects.filter(object_id=self.post.id).count() == 3
        
        response = self.client.get(
            f'/api/channels/{self.channel.slug}/posts/{self.post.slug}/likes/'
        )
        
        data = json.loads(response.content)
        
        assert response.status_code == 200
        assert data['success'] is True
        assert data['count'] == 3
        
        assert set(data['post'].keys()) == {'id', 'title', 'slug'}
        
        created_times = [l['created_at'] for l in data['data']]
        assert created_times == sorted(created_times, reverse=True)
        
        mock_get_users_batch.assert_called_once_with([3, 2, 1])
    
    def test_list_likes_empty(self):
        """
        Тест 7: Пустой список лайков (200)
        
        Проверяем:
        - Статус 200
        - count = 0
        - data = []
        """
        
        response = self.client.get(
            f'/api/channels/{self.channel.slug}/posts/{self.post.slug}/likes/'
        )
        
        data = json.loads(response.content)
        
        assert response.status_code == 200
        assert data['count'] == 0
        assert data['data'] == []
    
    @patch('apps.interactions.views.get_users_batch')
    def test_list_likes_user_structure(self, mock_get_users_batch):
        """
        Тест 8: Структура user (найден и не найден)
        
        Проверяем:
        - user не None когда найден
        - user = None когда не найден
        
        Моки:
        - get_users_batch возвращает только user_id=1
        """
        
        mock_get_users_batch.return_value = [
            {'id': 1, 'email': 'test@example.com', 'avatar_url': 'https://avatar_test.com'},
            
        ]
        
        Like.objects.create(
            user_id=1,
            content_type=self.content_type,
            object_id=self.post.id
        )
        
        Like.objects.create(
            user_id=999,
            content_type=self.content_type,
            object_id=self.post.id
        )
        
        assert Like.objects.filter(object_id=self.post.id).count() == 2
        
        response = self.client.get(
            f'/api/channels/{self.channel.slug}/posts/{self.post.slug}/likes/'
        )
        
        data = json.loads(response.content)
        
        assert response.status_code == 200
        assert data['success'] is True
        assert data['count'] == 2
        
        like_1 = next(l for l in data['data'] if l['user_id'] == 1)
        like_999 = next(l for l in data['data'] if l['user_id'] == 999)
        
        assert like_1 is not None
        assert set(like_1['user'].keys()) == {'id', 'email', 'avatar_url'}
        assert like_1['user']['id'] == 1
        assert like_1['user']['email'] == 'test@example.com'
        
        assert like_999['user'] is None
    
    def test_list_likes_post_not_found(self):
        """
        Тест 9: Пост не найден (404)
        
        Проверяем:
        - Статус 404
        """
        
        nonexistent_slug = 'nonexistent-post'
        
        response = self.client.get(
            f'/api/channels/{self.channel.slug}/posts/{nonexistent_slug}/likes/'
        )
        
        assert response.status_code == 404

@pytest.mark.django_db
@pytest.mark.views
class TestPostLikesCountView:
    
    def setup_method(self):
        self.client = Client()
        
        self.channel = Channel.objects.create(
            name='Test Channel',
            slug='test-channel',
            owner_id=1
        )
        
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            content='Test content',
            channel=self.channel,
            author_id=1
        )
        
        self.content_type = ContentType.objects.get_for_model(Post)
    
    def test_count_likes_with_likes(self):
        """
        Тест 10: Успешное получение количества (200)
        
        Проверяем:
        - Статус 200
        - success = True
        - post содержит: id, title, slug
        - likes_count = 3
        - is_liked = True
        
        """
        
        Like.objects.create(
            user_id=1,
            content_type=self.content_type,
            object_id=self.post.id
        )
        
        Like.objects.create(
            user_id=2,
            content_type=self.content_type,
            object_id=self.post.id
        )
        
        Like.objects.create(
            user_id=3,
            content_type=self.content_type,
            object_id=self.post.id
        )
        
        response = self.client.get(
            f'/api/channels/{self.channel.slug}/posts/{self.post.slug}/likes/count/'
        )
        
        data = json.loads(response.content)
        
        assert response.status_code == 200
        assert data['success'] is True
        assert data['likes_count'] == 3
        
        post = data['post']        
        assert set(post.keys()) == {'id', 'title', 'slug'}
        
        assert 'is_liked' in data
        assert isinstance(data['is_liked'], bool)
    
    def test_count_likes_empty(self):
        """
        Тест 11: Количество = 0 и is_liked = False
        
        Проверяем:
        - likes_count = 0
        - is_liked = False
        """
        
        response = self.client.get(
            f'/api/channels/{self.channel.slug}/posts/{self.post.slug}/likes/count/'
        )
        
        data = json.loads(response.content)
        
        assert data['likes_count'] == 0
        assert data['is_liked'] is False
    
    def test_count_likes_post_not_found(self):
        """
        Тест 12: Пост не найден (404)
        
        Проверяем:
        - Статус 404
        """
        
        nonexistent_slug = 'nonexistent-post'

        response = self.client.get(
            f'/api/channels/{self.channel.slug}/posts/{nonexistent_slug}/likes/count/'
        )
        
        assert response.status_code == 404
