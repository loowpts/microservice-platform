import pytest
import json
from django.test import Client
from apps.content.models import Channel
from apps.posts.models import Post
from apps.comments.models import Comment
from unittest.mock import patch


@pytest.mark.django_db
@pytest.mark.views
class TestCommentListView:
    """Тесты для GET /api/channels/{slug}/posts/{post_slug}/comments/"""
    
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
    
    @patch('apps.comments.views.get_users_batch')
    def test_list_comments_success(self, mock_get_users_batch):
        """
        Тест 1: Успешное получение списка комментариев
        
        Проверяем:
        - Статус 200
        - success = True
        - post содержит: id, title, slug
        - count = 2 (только корневые!)
        - data содержит список комментариев
        - Каждый комментарий: id, content, author_id, author, replies_count, replies, created_at
        - replies содержит ответы
        - Сортировка DESC
        
        Моки:
        - get_users_batch
        
        Подготовка:
        - Создать 2 корневых комментария
        - Создать 2 ответа на первый комментарий
        """
        mock_get_users_batch.return_value = [
            {'id': 1, 'email': 'test@example.com', 'avatar_url': 'https://avatar_test.com'},
            {'id': 2, 'email': 'test2@example.com', 'avatar_url': 'https://avatar_test.com'},
            {'id': 3, 'email': 'test3@example.com', 'avatar_url': 'https://avatar_test.com'}
        ]
        
        c1 = Comment.objects.create(
            post=self.post,
            author_id=1,
            content='First comment'
        )
        
        c2 = Comment.objects.create(
            post=self.post,
            author_id=2,
            content='Second comment'
        )
        
        assert Comment.objects.filter(post=self.post).count() == 2
        
        reply1 = Comment.objects.create(
            post=self.post,
            author_id=2,
            content='Reply 1',
            parent=c1
        )
        
        reply2 = Comment.objects.create(
            post=self.post,
            author_id=3,
            content='Reply 2',
            parent=c1
        )
        
        response = self.client.get(
            f'/api/channels/{self.channel.slug}/posts/{self.post.slug}/comments/'
        )
        
        data = json.loads(response.content)
        
        assert response.status_code == 200
        assert data['success'] is True
        
        assert set(data['post'].keys()) == {'id', 'title', 'slug'}
        assert data['post']['id'] == self.post.id
        assert data['count'] == 2
        assert len(data['data']) == 2
        
        comment = data['data'][0]
        assert set(comment.keys()) == {
            'id', 'content', 'author_id', 'author', 
            'replies_count', 'replies', 'created_at'
        }
        
        if comment['author']:
            assert set(comment['author'].keys()) == {'id', 'email', 'avatar_url'}

        comment_with_replies = next(c for c in data['data'] if c['id'] == c1.id)
        
        assert comment_with_replies['replies_count'] == 2
        
        assert len(comment_with_replies['replies']) == 2
        
        for reply in comment_with_replies['replies']:
            assert set(reply.keys()) == {
                'id', 'content', 'author_id', 'author', 'created_at'
            }
        
        created_times = [c['created_at'] for c in data['data']]
        assert created_times == sorted(created_times, reverse=True)
        
        mock_get_users_batch.assert_called_once()
        called_args = mock_get_users_batch.call_args[0][0]
        assert set(called_args) == {1, 2, 3}
        
    def test_list_comments_empty(self):
        """
        Тест 2: Пустой список комментариев
        
        Проверяем:
        - Статус 200
        - count = 0
        - data = []
        """
        pass
    
    @patch('apps.comments.views.get_users_batch')
    def test_list_comments_user_structure(self, mock_get_users_batch):
        """
        Тест 3: Структура user (найден и не найден)
        
        Проверяем:
        - user не None когда найден
        - user = None когда не найден
        
        Моки:
        - get_users_batch возвращает только user_id=1
        
        """
        pass
    
    def test_list_comments_post_not_found(self):
        """
        Тест 4: Пост не найден (404)
        
        Проверяем:
        - Статус 404
        """
        pass


@pytest.mark.django_db
@pytest.mark.views
class TestCommentCreateView:
    """Тесты для POST /api/channels/{slug}/posts/{post_slug}/comments/create/"""
    
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
    
    @patch('apps.comments.views.get_user')
    def test_create_comment_success(self, mock_get_user):
        """
        Тест 5: Успешное создание комментария
        
        Проверяем:
        - Статус 201
        - success = True
        - message = 'Комментарий успешно добавлен'
        - data содержит: id, content, author_id, author, replies_count, created_at
        - Comment создался в БД
        - author_id = request.user.id (= 1)
        
        Моки:
        - get_user
        
        """
        pass
    
    def test_create_comment_invalid_json(self):
        """
        Тест 6: Невалидный JSON
        
        Проверяем:
        - Статус 400
        - error = 'Невалидный Json'
        """
        pass
    
    def test_create_comment_invalid_data(self):
        """
        Тест 7: Невалидные данные
        
        Проверяем:
        - Статус 400
        - errors присутствуют
        - Comment НЕ создался
        
        """
        pass
    
    def test_create_comment_post_not_found(self):
        """
        Тест 8: Пост не найден (404)
        
        Проверяем:
        - Статус 404
        """
        pass


@pytest.mark.django_db
@pytest.mark.views
class TestCommentUpdateView:
    """Тесты для PATCH /api/channels/{slug}/posts/{post_slug}/comments/{comment_id}/"""
    
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
        
        self.comment = Comment.objects.create(
            post=self.post,
            author_id=1,
            content='Original content'
        )
    
    def test_update_comment_success(self):
        """
        Тест 9: Успешное обновление комментария
        
        Проверяем:
        - Статус 200
        - success = True
        - message = 'Комментарий обновлён'
        - content изменился в БД
        
        """
        pass
    
    def test_update_comment_not_author(self):
        """
        Тест 10: Не автор пытается обновить
        
        Проверяем:
        - Статус 403
        - code = 'permission_denied'
        - content НЕ изменился
        
        """
        pass
    
    def test_update_comment_invalid_json(self):
        """
        Тест 11: Невалидный JSON
        
        Проверяем:
        - Статус 400
        - error = 'Невалидный Json'
        """
        pass


@pytest.mark.django_db
@pytest.mark.views
class TestCommentDeleteView:
    """Тесты для DELETE /api/channels/{slug}/posts/{post_slug}/comments/{comment_id}/delete/"""
    
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
        
        self.comment = Comment.objects.create(
            post=self.post,
            author_id=1,
            content='Test comment'
        )
    
    def test_delete_comment_success(self):
        """
        Тест 12: Успешное удаление комментария
        
        Проверяем:
        - Статус 200
        - success = True
        - message = 'Комментарий удалён'
        - Comment удалился из БД
        
        """
        pass
    
    def test_delete_comment_not_author(self):
        """
        Тест 13: Не автор пытается удалить
        
        Проверяем:
        - Статус 403
        - code = 'permission_denied'
        - Comment НЕ удалился
        
        """
        pass
    
    def test_delete_comment_not_found(self):
        """
        Тест 14: Комментарий не найден (404)
        
        Проверяем:
        - Статус 404
        """
        pass


@pytest.mark.django_db
@pytest.mark.views
class TestCommentReplyView:
    """Тесты для POST /api/channels/{slug}/posts/{post_slug}/comments/{comment_id}/reply/"""
    
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
        
        self.comment = Comment.objects.create(
            post=self.post,
            author_id=2,
            content='Parent comment'
        )
    
    @patch('apps.comments.views.get_user')
    def test_reply_comment_success(self, mock_get_user):
        """
        Тест 15: Успешный ответ на комментарий
        
        Проверяем:
        - Статус 201
        - success = True
        - message = 'Ответ добавлен'
        - data содержит: id, content, author_id, author, parent_id, created_at
        - Reply создался в БД с правильным parent
        - parent.replies.count() увеличился
        
        Моки:
        - get_user
        
        """
        pass
    
    def test_reply_to_reply_forbidden(self):
        """
        Тест 16: Ответ на ответ (запрещено)
        
        Проверяем:
        - Статус 400
        - error = 'Нельзя отвечать на ответ'
        - code = 'invalid_parent'
        - Comment НЕ создался
        
        """
        pass
    
    def test_reply_comment_invalid_data(self):
        """
        Тест 17: Невалидные данные
        
        Проверяем:
        - Статус 400
        - errors присутствуют
        
        - content слишком короткий
        """
        pass
    
    def test_reply_comment_not_found(self):
        """
        Тест 18: Родительский комментарий не найден (404)
        
        Проверяем:
        - Статус 404
        """
        pass
