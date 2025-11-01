import pytest
import json
from django.test import Client
from apps.content.models import Channel, ChannelRole
from apps.posts.models import Post
from apps.comments.models import Comment
from apps.memberships.models import ChannelMembership
from apps.interactions.models import Like, View
from unittest.mock import patch

class TestPostListView:
    
    def setup_method(self):
        """Выполняется перед каждым тестом"""
        self.client = Client()
        
        self.channel = Channel.objects.create(
            name='Test Channel',
            slug='test-channel',
            owner_id=1
        )
    
    @patch('apps.posts.views.get_users_batch')
    def test_list_posts_success(self, mock_get_users_batch):
        """
        Тест: Успешное получение списка постов канала
        
        Проверяем:
        - Статус 200
        - success = True
        - channel содержит: id, name, slug
        - count соответствует количеству постов
        - data содержит список постов
        - Каждый пост: id, title, slug, content (обрезанный!), author_id, author, 
          image_url, comments_count, created_at
        - author содержит: id, email, avatar_url
        - content обрезан до 200 символов + '...' (если длиннее)
        
        Моки:
        - get_users_batch - возвращает авторов постов
        
        """
        mock_get_users_batch.return_value = [
            {'id': 1, 'username': 'user1', 'email': 'test@example.com'},
            {'id': 2, 'username': 'user2', 'email': 'test2@example.com'}
        ]
        
        Post.objects.create(
            channel=self.channel,
            title='Test One',
            slug='test-one',
            content='Test content',
            author_id=1
        )
        
        Post.objects.create(
            channel=self.channel,
            title='Test two',
            slug='test-two',
            content='Test content',
            author_id=1
        )
        
        Post.objects.create(
            channel=self.channel,
            title='Test three',
            slug='test-three',
            content='Test content',
            author_id=1
        )
        
        response = self.client.get(f'/api/channels/{self.channel.slug}/posts/')
        data = json.loads(response.content)
        
        assert response.status_code == 200
        assert data['success'] == True
        assert data['count'] == 3
        assert data['channel']['slug'] == 'test-channel'
        assert 'author' in data['data'][0]
        assert data['data'][0]['author']['id'] == 1
        
    def test_list_posts_empty(self):
        """
        Тест: Пустой список постов
        
        Проверяем:
        - Статус 200
        - success = True
        - count = 0
        - data = []
        - channel присутствует
        
        Подготовка:
        - Канал существует, но постов нет
        """
        response = self.client.get(f'/api/channels/{self.channel.slug}/posts/')
        data = json.loads(response.content)
        
        assert response.status_code == 200
        assert data['success'] == True
        assert data['count'] == 0
        assert data['data'] == []
        assert Channel.objects.count() == 1
        assert Post.objects.count() == 0
        
    
    def test_list_posts_channel_not_found(self):
        """
        Тест: Канал не найден (404)
        
        Проверяем:
        - Статус 404
        
        Подготовка:
        - Запросить несуществующий channel_slug
        """
        nonexistent_slug = 'nonexistent-channel'
        
        assert not Channel.objects.filter(slug=nonexistent_slug)
        
        response = self.client.get(f'/api/channels/{nonexistent_slug}/posts/')
        
        assert response.status_code == 404
        
    
    @patch('apps.posts.views.get_users_batch')
    def test_list_posts_content_truncated(self, mock_get_users_batch):
        """
        Тест: Content обрезается до 200 символов
        
        Проверяем:
        - Длинный content (>200) обрезан до 200 + '...'
        - Короткий content (<200) остается без изменений
        
        """
        mock_get_users_batch.return_value = [
            {'id': 1, 'username': 'user1', 'email': 'test@example.com'}
        ]
        
        long_content = 'A' * 300
        Post.objects.create(
            channel=self.channel,
            title='Long Post',
            slug='long-post',
            content=long_content,
            author_id=1
        )
        
        short_content = 'Short content here'
        Post.objects.create(
            channel=self.channel,
            title='Short Post',
            slug='short-post',
            content=short_content,
            author_id=1
        )
        
        response = self.client.get(f'/api/channels/{self.channel.slug}/posts/')
        data = json.loads(response.content)
        
        assert response.status_code == 200
        assert data['success'] == True
        
        long_post = next(p for p in data['data'] if p['slug'] == 'long-post')
        short_post = next(p for p in data['data'] if p['slug'] == 'short-post')
        
        assert len(long_post['content']) == 203
        assert long_post['content'].endswith('...')
        
        assert short_post['content'] == short_content
        assert not short_post['content'].endswith('...')
        
    @patch('apps.posts.views.get_users_batch')
    def test_list_posts_author_structure(self, mock_get_users_batch):
        """
        Тест: Структура автора
        
        Проверяем:
        - author не None когда найден в User Service
        - author = None когда не найден
        - author содержит: id, email, avatar_url
        
        Моки:
        - get_users_batch возвращает только некоторых авторов
        
        """
        mock_get_users_batch.return_value = [
            {'id': 1, 'email': 'test@example.com', 'avatar_url': 'https://avatarurl.net'},
            {'id': 2, 'email': 'test1@example.com', 'avatar_url': 'https://avatarurl.net'}
        ]
        
        Post.objects.create(
            channel=self.channel,
            title='Long Post',
            slug='post-1',
            content='long_content',
            author_id=1
        )
        
        Post.objects.create(
            channel=self.channel,
            title='Post 2',
            slug='post-2',
            content='Content 2',
            author_id=999
        )
        
        response = self.client.get(f'/api/channels/{self.channel.slug}/posts/')
        data = json.loads(response.content)
        
        assert response.status_code == 200
        assert data['success'] == True
        assert data['count'] == 2

        post1 = next(p for p in data['data'] if p['slug']== 'post-1')
        post2 = next(p for p in data['data'] if p['slug']== 'post-2')
        
        assert post1['author'] is not None
        assert post1['id'] == 1
        assert post1['author']['email'] == 'test@example.com'
        assert 'avatar_url' in post1['author']
        assert post1['author']['avatar_url'] == 'https://avatarurl.net'
        
        assert post2['author'] is None
        assert post2['author_id'] == 999
        
    @patch('apps.posts.views.get_users_batch')
    def test_list_posts_comments_count(self, mock_get_users_batch):
        """
        Тест: comments_count правильный
        
        Проверяем:
        - comments_count соответствует реальному количеству комментариев
        
        """
        mock_get_users_batch.return_value = [
            {'id': 1, 'email': 'test@example.com'}
        ]
        
        post = Post.objects.create(
            channel=self.channel,
            title='Long Post',
            slug='post-1',
            content='long_content',
            author_id=1
        )
        
        Comment.objects.create(
            post=post,
            content='Test content1',
            author_id=2
        )

        Comment.objects.create(
            post=post,
            content='Test content2',
            author_id=2
        )
        
        Comment.objects.create(
            post=post,
            content='Test content3',
            author_id=2
        )
        
        response = self.client.get(f'/api/channels/{self.channel.slug}/posts/')
        
        assert response.status_code == 200
        assert Comment.objects.filter(post=post).count() == 3


@pytest.mark.django_db
@pytest.mark.views
class TestPostCreateView:
    
    def setup_method(self):
        """Выполняется перед каждым тестом"""
        self.client = Client()
        
        self.channel = Channel.objects.create(
            name='Test Channel',
            slug='test-channel',
            owner_id=1
        )
    
    @patch('apps.posts.views.get_user')
    def test_create_post_success(self, mock_get_user):
        """
        Тест: Успешное создание поста (участник канала)
        
        Проверяем:
        - Статус 201
        - success = True
        - message = 'Пост успешно создан.'
        - data содержит: id, title, slug, content, channel, author, created_at
        - Пост реально создался в БД
        - author_id = request.user.id
        - channel правильный
        
        Моки:
        - get_user - возвращает данные автора
        
        """
        mock_get_user.return_value = {
            'id': 1, 
            'email': 'test@example.com'
        }
        
        ChannelMembership.objects.create(
            channel=self.channel,
            user_id=1,
            role=ChannelRole.MEMBER
        )
        
        data = {
            'title': 'New Post',
            'content': 'Test content new'
        }
        
        assert Post.objects.count() == 0
        
        response = self.client.post(
            f'/api/channels/{self.channel.slug}/posts/create/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        response_data = json.loads(response.content)
        
        assert response.status_code == 201
        assert response_data['success'] == True
        assert response_data['message'] == 'Пост успешно создан.'
        
        assert Post.objects.count() == 1
        assert Post.objects.filter(slug='new-post').exists()    

        post = Post.objects.get(slug='new-post')
        assert post.title == 'New Post'
        assert post.author_id == 1
        
    def test_create_post_not_member(self):
        """
        Тест: Создание поста без membership (403)
        
        Проверяем:
        - Статус 403
        - success = False
        - error = 'Вы не являетесь членом этого канала'
        - code = 'not_a_member'
        - Пост НЕ создался в БД
        
        """
        
        data = {
            'title': 'New Post',
            'content': 'Test content new'
        }
        
        assert Post.objects.count() == 0
        
        response = self.client.post(
            f'/api/channels/{self.channel.slug}/posts/create/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        response_data = json.loads(response.content)
        
        assert response.status_code == 403
        assert response_data['success'] == False
        assert response_data['error'] == 'Вы не являетесь членом этого канала'
        assert response_data['code'] == 'not_a_member'
        assert Post.objects.filter(channel=self.channel).count() == 0
    
    @patch('apps.posts.views.get_user')
    def test_create_post_without_title(self, mock_get_user):
        """
        Тест: Создание без обязательного поля title
        
        Проверяем:
        - Статус 400
        - success = False
        - error = 'Ошибка валидации'
        - errors содержит 'title'
        - Пост НЕ создался
        """
        mock_get_user.return_value = {
            'id': 1, 
            'email': 'test@example.com'
        }
        
        ChannelMembership.objects.create(
            channel=self.channel,
            user_id=1,
            role=ChannelRole.MEMBER
        )
        
        data = {
            'content': 'Test content new',
        }
        
        assert Post.objects.count() == 0
        
        response = self.client.post(
            f'/api/channels/{self.channel.slug}/posts/create/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        response_data = json.loads(response.content)
        
        assert response.status_code == 400
        assert response_data['success'] == False
        assert response_data['error'] == 'Ошибка валидации'
        assert 'title' in response_data['errors']
        assert Post.objects.filter(channel=self.channel).count() == 0
        
    @patch('apps.posts.views.get_user')
    def test_create_post_without_content(self, mock_get_user):
        """
        Тест: Создание без обязательного поля content
        
        Проверяем:
        - Статус 400
        - errors содержит 'content'
        - Пост НЕ создался
        
        """
        mock_get_user.return_value = {
            'id': 1, 
            'email': 'test@example.com'
        }
        
        ChannelMembership.objects.create(
            channel=self.channel,
            user_id=1,
            role=ChannelRole.MEMBER
        )
        
        data = {
            'name': 'Test content new',
        }
        
        assert Post.objects.count() == 0
        
        response = self.client.post(
            f'/api/channels/{self.channel.slug}/posts/create/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        response_data = json.loads(response.content)
        
        assert response.status_code == 400
        assert response_data['success'] == False
        assert response_data['error'] == 'Ошибка валидации'
        assert 'title' in response_data['errors']
        assert Post.objects.filter(channel=self.channel).count() == 0
        
    def test_create_post_invalid_json(self):
        """
        Тест: Невалидный JSON
        
        Проверяем:
        - Статус 400
        - error = 'Невалидный Json'
        
        """       
        ChannelMembership.objects.create(
            channel=self.channel,
            user_id=1,
            role=ChannelRole.MEMBER
        )
        
        response = self.client.post(
            f'/api/channels/{self.channel.slug}/posts/create/',
            data='this is not json',
            content_type='application/json'
        )
        
        response_data = json.loads(response.content)
        
        assert response.status_code == 400
        assert response_data['success'] is False
        assert response_data['error'] == 'Невалидный Json'

@pytest.mark.django_db
@pytest.mark.views
class TestPostDetailView:
 
    def setup_method(self):
        """Выполняется перед каждым тестом"""
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
    
    @patch('apps.posts.views.get_user')
    def test_retrieve_post_success(self, mock_get_user):
        """
        Тест: Успешное получение деталей поста
        
        Проверяем:
        - Статус 200
        - success = True
        - data содержит: id, title, slug, content (полный!), author_id, author, 
          image_url, channel, views_count, comments_count, created_at, updated_at
        - author с id, email, avatar_url
        - channel с id, slug, name
        - content НЕ обрезан (полный)
        
        Моки:
        - get_user - для данных автора
        """
        mock_get_user.return_value = {
            'id': 1,
            'email': 'test@example.com',
            'avatar_url': 'https://test_url.com'
        }
        
        response = self.client.get(f'/api/channels/{self.channel.slug}/posts/{self.post.slug}/')
        data = json.loads(response.content)
        
        assert response.status_code == 200
        assert data['success'] is True
        
        assert data['data']['title'] == 'Test Post'
        assert data['data']['content'] == 'Test content'
        
        assert data['data']['author']['id'] == 1
        assert data['data']['author']['email'] == 'test@example.com'
        
        assert data['data']['channel']['slug'] == 'test-channel'
        
        assert data['data']['views_count'] >= 1
        assert data['data']['comments_count'] == 0
            
    
    @patch('apps.posts.views.get_user')
    def test_retrieve_post_creates_view(self, mock_get_user):
        """
        Тест: Создание записи просмотра (View)
        
        Проверяем:
        - View запись создалась в БД
        - user_id = request.user.id
        - ip_address сохранился
        - user_agent сохранился
        - View.objects.count() увеличился на 1
        
        """
        mock_get_user.return_value = {
            'id': 1,
            'email': 'test@example.com'
        }

        initial_count = View.objects.filter(post=self.post).count()
        assert initial_count == 0

        response = self.client.get(f'/api/channels/{self.channel.slug}/posts/{self.post.slug}/')
        data = json.loads(response.content)
        
        final_count = View.objects.filter(post=self.post).count()
        assert final_count == initial_count + 1
        assert final_count == 1
        
        assert View.objects.filter(post=self.post).exists()
        view = View.objects.filter(post=self.post).last()
        assert view.user_id == 1
        assert view.ip_address is not None
        assert isinstance(view.ip_address, str)
        assert view.user_agent is not None
        assert isinstance(view.user_agent, str)
        assert len(view.user_agent) >= 0
        
    @patch('apps.posts.views.get_user')
    def test_retrieve_post_views_count_increases(self, mock_get_user):
        """
        Тест: views_count увеличивается
        
        Проверяем:
        - При каждом запросе views_count растет
        - Даже если один пользователь запрашивает несколько раз
    
        """
        mock_get_user.return_value = {
            'id': 1,
            'email': 'test@example.com'
        }

        for i in range(1, 4):
            response = self.client.get(
                f'/api/channels/{self.channel.slug}/posts/{self.post.slug}/'
                )
            data = json.loads(response.content)
        
        assert response.status_code == 200
        assert data['data']['views_count'] == i
        
        
    def test_retrieve_post_not_found(self):
        """
        Тест: Пост не найден (404)
        
        Проверяем:
        - Статус 404
        
        """
        nonexistent_slug = 'nonexistent-post'
        
        assert not Post.objects.filter(slug=nonexistent_slug)
        
        response = self.client.get(f'/api/channels/{self.channel.slug}/posts/{nonexistent_slug}/')
        
        assert response.status_code == 404
    
    @patch('apps.posts.views.get_user')
    def test_retrieve_post_wrong_channel(self, mock_get_user):
        mock_get_user.return_value = {'id': 1, 'email': 'test@example.com'}
        
        channel_a = Channel.objects.create(
            name='Channel A',
            slug='channel-a',
            owner_id=1
        )
        
        post_x = Post.objects.create(
            title='Post X',
            slug='post-x',
            content='Content X',
            channel=channel_a,
            author_id=1
        )
        
        channel_b = Channel.objects.create(
            name='Channel B',
            slug='channel-b',
            owner_id=1
        )
        
        response = self.client.get(f'/api/channels/{channel_b.slug}/posts/{post_x.slug}/')
        
        assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.views
class TestPostUpdateView:
    
    def setup_method(self):
        """Выполняется перед каждым тестом"""
        self.client = Client()
        
        self.channel = Channel.objects.create(
            name='Test Channel',
            slug='test-channel',
            owner_id=1
        )
        
        self.post = Post.objects.create(
            title='Old TitleOldOld',
            slug='test-post',
            content='Old content',
            channel=self.channel,
            author_id=1
        )
        
        self.membership = ChannelMembership.objects.create(
            channel=self.channel,
            user_id=1,
            role=ChannelRole.MEMBER
        )
    
    def test_update_post_success(self):
        """
        Тест: Успешное обновление поста (автор)
        
        Проверяем:
        - Статус 200
        - success = True
        - message = 'Пост успешно обновлён.'
        - Изменения сохранились в БД (refresh_from_db!)
        - updated_at изменился
        
        """
        update_data = {
            'title': 'New title',
            'content': 'New content',
        }
        
        response = self.client.patch(
            f'/api/channels/{self.channel.slug}/posts/{self.post.slug}/update/',
            data=json.dumps(update_data),
            content_type='application/json'
            )
        
        response_data = json.loads(response.content)
        
        assert response.status_code == 200
        assert response_data['success'] == True
        assert response_data['message'] == 'Пост успешно обновлён.'

        self.post.refresh_from_db()
        assert self.post.title == 'New title'
        assert self.post.content == 'New content'
        
    def test_update_post_partial(self):
        """Тест: Частичное обновление (только title)"""
        
        old_content = self.post.content
        
        update_data = {
            'title': 'New Title'
        }
        
        response = self.client.patch(
            f'/api/channels/{self.channel.slug}/posts/{self.post.slug}/update/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        
        self.post.refresh_from_db()
        
        assert self.post.title == 'New Title'
        
        assert self.post.content == old_content
        assert self.post.content == 'Old content'
    
    def test_update_post_forbidden(self):
        """
        Тест: Обновление чужого поста (не автор, не модератор) - 403
        """

        self.post.author_id = 999
        self.post.save()
        
        old_title = self.post.title
        old_content = self.post.content
        
        update_data = {
            'title': 'Hacked Title',
            'content': 'Hacked Content'
        }
        
        response = self.client.patch(
            f'/api/channels/{self.channel.slug}/posts/{self.post.slug}/update/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        response_data = json.loads(response.content)
        
        assert response.status_code == 403
        assert response_data['success'] is False
        assert response_data['code'] == 'permission_denied'
        assert 'прав' in response_data['error'].lower() or 'permission' in response_data['error'].lower()
        
        self.post.refresh_from_db()
        assert self.post.title == old_title
        assert self.post.content == old_content

    def test_update_post_by_moderator(self):
        """
        Тест: Обновление модератором (если role=MODERATOR может)
        """
        self.post.author_id = 999
        self.post.save()
        
        self.membership.role = ChannelRole.MODERATOR
        self.membership.save()
        
        update_data = {
            'title': 'Updated by Moderator',
            'content': 'Moderator content'
        }
        
        response = self.client.patch(
            f'/api/channels/{self.channel.slug}/posts/{self.post.slug}/update/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        if self.post.can_edit(1, ChannelRole.MODERATOR):
            assert response.status_code == 200
            
            self.post.refresh_from_db()
            assert self.post.title == 'Updated by Moderator'
        else:
            assert response.status_code == 403

    def test_update_post_without_membership(self):
        """
        Тест: Обновление без membership (403)
        """
        self.post.author_id = 999
        self.post.save()
        
        self.membership.delete()
        
        old_content = self.post.content
        
        update_data = {
            'title': 'New Title'
        }
        
        response = self.client.patch(
            f'/api/channels/{self.channel.slug}/posts/{self.post.slug}/update/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        response_data = json.loads(response.content)
        
        assert response.status_code == 403
        assert response_data['code'] == 'permission_denied'

        self.post.refresh_from_db()
        assert self.post.content == old_content

    def test_update_post_not_found(self):
        """
        Тест: Пост не найден (404)
        """
        update_data = {
            'title': 'New Title'
        }
        
        response = self.client.patch(
            f'/api/channels/{self.channel.slug}/posts/nonexistent-post/update/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 404

    def test_update_post_invalid_data(self):
        """
        Тест: Невалидные данные (400)
        """
        old_title = self.post.title
        old_content = self.post.content
        
        update_data = {
            'title': 'ab',
            'content': 'abc'
        }
        
        response = self.client.patch(
            f'/api/channels/{self.channel.slug}/posts/{self.post.slug}/update/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        response_data = json.loads(response.content)
        
        assert response.status_code == 400
        assert response_data['success'] is False
        assert 'errors' in response_data
        
        assert 'title' in response_data['errors'] or 'content' in response_data['errors']
        
        self.post.refresh_from_db()
        assert self.post.title == old_title
        assert self.post.content == old_content

    def test_update_post_invalid_json(self):
        """
        Тест: Невалидный JSON
        """

        response = self.client.patch(
            f'/api/channels/{self.channel.slug}/posts/{self.post.slug}/update/',
            data='not a json',
            content_type='application/json'
        )
        
        response_data = json.loads(response.content)
        
        assert response.status_code == 400
        assert response_data['success'] is False
        assert response_data['error'] == 'Невалидный Json'

@pytest.mark.django_db
@pytest.mark.views
class TestPostDeleteView:
    
    def setup_method(self):
        self.client = Client()
        
        self.channel = Channel.objects.create(
            name='Test Channel',
            slug='test-channel',
            owner_id=1
        )
        
        self.post = Post.objects.create(
            title='To Delete',
            slug='test-post',
            content='Test content',
            channel=self.channel,
            author_id=1
        )
        
        self.membership = ChannelMembership.objects.create(
            channel=self.channel,
            user_id=1,
            role=ChannelRole.MEMBER
        )
    
    def test_delete_post_success(self):
        """
        Тест: Успешное удаление поста (автор)
        
        Проверяем:
        - Статус 200
        - success = True
        - message содержит название поста
        - data содержит: id, title, slug, channel
        - Пост реально удалился из БД
        """
        
        response = self.client.delete(
            f'/api/channels/{self.channel.slug}/posts/{self.post.slug}/delete/'
            )
        data = json.loads(response.content)
        assert response.status_code == 200
        assert data['success'] is True
        assert data['data']['id'] is not None
        assert data['data']['title'] is not None
        assert data['data']['slug'] is not None
        assert data['data']['channel'] is not None
        check_post = Post.objects.filter(channel=self.channel)
        assert check_post.count() == 0
        

    def test_delete_post_forbidden(self):
        """
        Тест: Удаление чужого поста (403)
        
        Проверяем:
        - Статус 403
        - success = False
        - code = 'permission_denied'
        - Пост НЕ удалился из БД
        
        """
        self.post.author_id = 999
        self.post.save()
        response = self.client.delete(
            f'/api/channels/{self.channel.slug}/posts/{self.post.slug}/delete/'
            )
        
        data = json.loads(response.content)
        
        assert response.status_code == 403
        assert data['code'] == 'permission_denied'
        assert data['error'] == 'У вас нет прав для удаления этого поста.'
        
        self.post.refresh_from_db()
        assert Post.objects.filter(slug='test-post').exists()
        assert Post.objects.count() == 1
    
    def test_delete_post_by_moderator(self):
        """
        Тест: Удаление модератором (если может)
        
        Проверяем:
        - Статус 200
        - Пост удалился
        """
        self.post.author_id = 999
        self.post.save()
        
        response = self.client.delete(
            f'/api/channels/{self.channel.slug}/posts/{self.post.slug}/delete/'
        )
        data = json.loads(response.content)
        
        if self.post.can_edit(1, ChannelRole.MODERATOR):
            assert response.status_code == 200
            assert data['success'] is True
            
            assert not Post.objects.filter(channel=self.channel).exists()
            assert Post.objects.filter(slug='test-post').exists()
        
        
    def test_delete_post_without_membership(self):
        """
        Тест: Удаление без membership (403)
        
        Проверяем:
        - Статус 403
        - Пост НЕ удалился
        """
        self.post.author_id = 999
        self.post.save()
         
        self.membership.delete()
        
        response = self.client.delete(
            f'/api/channels/{self.channel.slug}/posts/{self.post.slug}/delete/'
        )
        
        assert response.status_code == 403
        
        assert Post.objects.filter(slug='test-post').exists()

    def test_delete_post_not_found(self):
        """
        Тест: Пост не найден (404)
        
        Проверяем:
        - Статус 404
        
        """
        
        response = self.client.delete(
            f'/api/channels/{self.channel.slug}/posts/nonexistent-post/delete/'
        )

        assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.views
class TestPostSearchView:
    
    def setup_method(self):
        self.client = Client()
        
        self.channel = Channel.objects.create(
            name='Test Channel',
            slug='test-channel',
            owner_id=1
        )
    
    @patch('apps.posts.views.get_users_batch')
    def test_search_posts_by_title(self, mock_get_users_batch):
        """
        Тест: Успешный поиск по title
        """
        mock_get_users_batch.return_value = [
            {'id': 1, 'username': 'user1', 'email': 'test@example.com'}
        ]
        
        Post.objects.create(
            title='Python Tutorial',
            slug='python-tutorial',
            content='Content about Python',
            channel=self.channel,
            author_id=1
        )
        Post.objects.create(
            title='Django Guide',
            slug='django-guide',
            content='Content about Django',
            channel=self.channel,
            author_id=1
        )
        Post.objects.create(
            title='React Basics',
            slug='react-basics',
            content='Content about React',
            channel=self.channel,
            author_id=1
        )
        
        response = self.client.get('/api/posts/search/?query=Python')
        data = json.loads(response.content)
        
        assert response.status_code == 200
        assert data['success'] is True
        assert data['query'] == 'Python'
        assert data['count'] == 1
        assert len(data['data']) == 1
        assert data['data'][0]['title'] == 'Python Tutorial'

    @patch('apps.posts.views.get_users_batch')
    def test_search_posts_by_content(self, mock_get_users_batch):
        """
        Тест: Поиск по content
        """
        mock_get_users_batch.return_value = [{'id': 1, 'username': 'user1'}]
        
        Post.objects.create(
            title='Programming Tutorial',
            slug='programming',
            content='This is about Python programming',
            channel=self.channel,
            author_id=1
        )
        Post.objects.create(
            title='Web Development',
            slug='web-dev',
            content='This is about JavaScript',
            channel=self.channel,
            author_id=1
        )
        
        response = self.client.get('/api/posts/search/?query=Python')
        data = json.loads(response.content)
        
        assert response.status_code == 200
        assert data['count'] == 1
        assert data['data'][0]['slug'] == 'programming'
        assert 'Python' in data['data'][0]['content']

    @patch('apps.posts.views.get_users_batch')
    def test_search_posts_case_insensitive(self, mock_get_users_batch):
        """
        Тест: Поиск регистронезависимый
        """
        mock_get_users_batch.return_value = [{'id': 1, 'username': 'user1'}]
        
        Post.objects.create(
            title='Python Tutorial',
            slug='python',
            content='About Python',
            channel=self.channel,
            author_id=1
        )
        
        for query in ['python', 'PYTHON', 'PyThOn', 'Python']:
            response = self.client.get(f'/api/posts/search/?query={query}')
            data = json.loads(response.content)
            
            assert response.status_code == 200
            assert data['count'] == 1
            assert data['data'][0]['title'] == 'Python Tutorial'

    def test_search_posts_without_query(self):
        """
        Тест: Поиск без query (400)
        """
        response = self.client.get('/api/posts/search/')
        data = json.loads(response.content)
        
        assert response.status_code == 400
        assert data['success'] is False
        assert 'error' in data
        assert 'query' in data['error'].lower() or 'обязателен' in data['error'].lower()
        assert 'errors' in data

    @patch('apps.posts.views.get_users_batch')
    def test_search_posts_no_results(self, mock_get_users_batch):
        """
        Тест: Поиск ничего не нашел
        """
        mock_get_users_batch.return_value = []
        
        Post.objects.create(
            title='Python Tutorial',
            slug='python',
            content='Python content',
            channel=self.channel,
            author_id=1
        )
        
        response = self.client.get('/api/posts/search/?query=NonExistentQuery')
        data = json.loads(response.content)
        
        assert response.status_code == 200
        assert data['success'] is True
        assert data['query'] == 'NonExistentQuery'
        assert data['count'] == 0
        assert len(data['data']) == 0
        assert data['data'] == []

    @patch('apps.posts.views.get_users_batch')
    def test_search_posts_limited_to_50(self, mock_get_users_batch):
        """
        Тест: Поиск ограничен 50 результатами
        """
        mock_get_users_batch.return_value = []
        
        for i in range(60):
            Post.objects.create(
                title=f'Python Tutorial {i}',
                slug=f'python-{i}',
                content='Python programming',
                channel=self.channel,
                author_id=1
            )
        
        response = self.client.get('/api/posts/search/?query=Python')
        data = json.loads(response.content)
        
        assert response.status_code == 200
        assert data['count'] == 50
        assert len(data['data']) == 50

    @patch('apps.posts.views.get_users_batch')
    def test_search_posts_content_truncated(self, mock_get_users_batch):
        """
        Тест: Content обрезается в результатах поиска
        """
        mock_get_users_batch.return_value = [{'id': 1, 'username': 'user1'}]
        
        long_content = 'Python ' + 'A' * 300
        Post.objects.create(
            title='Long Post',
            slug='long-post',
            content=long_content,
            channel=self.channel,
            author_id=1
        )
        
        response = self.client.get('/api/posts/search/?query=Python')
        data = json.loads(response.content)
        
        assert response.status_code == 200
        assert data['count'] == 1
        
        assert len(data['data'][0]['content']) == 203  # 200 + '...'
        assert data['data'][0]['content'].endswith('...')
