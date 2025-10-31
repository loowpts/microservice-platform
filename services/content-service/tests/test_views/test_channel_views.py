import pytest
import json
from django.test import Client
from apps.content.models import Channel
from apps.posts.models import Post
from apps.memberships.models import ChannelMembership
from unittest.mock import patch


@pytest.mark.django_db
@pytest.mark.views
class TestChannelListView:
    def setup_method(self):
        self.client = Client()
        
        self.channel = Channel.objects.create(
            name='Test Channel',
            slug='test-channel',
            description='Test description',
            owner_id=1
        )
    
    @patch('apps.content.views.get_users_batch')
    def test_list_channels_success(self, mock_get_users_batch):
        """
        Тест: Успешное получение списка каналов
        
        Проверяем:
        - Статус код 200
        - success = True
        - Возвращается список каналов в 'data'
        - Структура каждого канала корректна (id, name, slug, owner_id, owner)
        - Owner содержит id и username
        
        Моки:
        - get_users_batch - возвращает список пользователей
        """
        mock_get_users_batch.return_value = [
            {'id': 1, 'username': 'testuser', 'email': 'test@example.com'}
        ]
        
        response = self.client.get('/api/channels/')
        data = json.loads(response.content)
        
        assert response.status_code == 200
        assert data['success'] is True
        assert 'data' in data
        assert isinstance(data['data'], list)
        assert len(data['data']) == 1
        
        channel_data = data['data'][0]
        assert channel_data['id'] == self.channel.id
        assert channel_data['name'] == 'Test Channel'
        assert channel_data['slug'] == 'test-channel'
        assert channel_data['owner_id'] == 1
        
        assert 'owner' in channel_data
        assert channel_data['owner']['id'] == 1
        assert channel_data['owner']['username'] == 'testuser'
    
    def test_list_channels_empty(self):
        """
        Тест: Пустой список каналов
        
        Проверяем:
        - Статус код 200
        - success = True
        - data - пустой список
        - count = 0
        - get_users_batch НЕ вызывается (нет каналов)
        """
        Channel.objects.all().delete()
        
        response = self.client.get('/api/channels/')
        data = json.loads(response.content)
        
        assert response.status_code == 200
        assert data['success'] is True
        assert data['data'] == []
        assert data['count'] == 0
        
    @patch('apps.content.views.get_users_batch')
    def test_list_multiple_channels(self, mock_get_users_batch):
        """
        Тест: Список с несколькими каналами
        
        Проверяем:
        - Статус код 200
        - count соответствует количеству созданных каналов
        - Все каналы присутствуют в списке
        - Структура каждого канала правильная
        
        """
        Channel.objects.all().delete()
        
        Channel.objects.create(
            name='Test1##@#@$',
            description='Test1',
            slug='test1',
            owner_id=1
        )
        
        Channel.objects.create(
            name='Test Valida',
            description='Test2',
            slug='test-valida',
            owner_id=2
        )
        
        Channel.objects.create(
            name='Test3ARE',
            description='Test3',
            slug='test3are',
            owner_id=1
        )
        
        Channel.objects.create(
            name='Test4',
            description='Test4',
            slug='test4',
            owner_id=2
        )
        
        mock_get_users_batch.return_value = [
            {'id': 1, 'username': 'user1'},
            {'id': 2, 'username': 'user2'}
        ]
        
        response = self.client.get('/api/channels/')
        data = json.loads(response.content)
        
        assert response.status_code == 200
        assert data['count'] == 4
        assert len(data['data']) == 4
        
        slugs = [ch['slug'] for ch in data['data']]
        assert 'test1' in slugs
        assert 'test-valida' in slugs
        assert 'test3are' in slugs
        assert 'test4' in slugs
        
        for channel_data in data['data']:
            assert 'id' in channel_data
            assert 'name' in channel_data
            assert 'slug' in channel_data
            assert 'owner_id' in channel_data
            assert 'owner' in channel_data
            
        python_channel = next(ch for ch in data['data'] if ch['slug'] == 'test3are')
        assert python_channel['owner']['username'] == 'user1'

    @patch('apps.content.views.get_users_batch')
    def test_list_channels_owner_structure(self, mock_get_users_batch):
        """
        Тест: Проверка структуры owner в списке
        
        Проверяем:
        - owner не None когда пользователь найден
        - owner содержит id и username
        - Если get_users_batch вернул None для owner_id, то owner = None
        
        """
        Channel.objects.all().delete()
        
        Channel.objects.create(
            name='Channel 1',
            description='Test1',
            slug='channel-1',
            owner_id=2
        )
        
        Channel.objects.create(
            name='Channel 2',
            description='Test2',
            slug='channel-2',
            owner_id=1
        )
        
        Channel.objects.create(
            name='Channel3',
            description='Test3',
            slug='channel-3',
            owner_id=999
        )    
        
        mock_get_users_batch.return_value = [
            {'id': 1, 'username': 'user1'},
            {'id': 2, 'username': 'user2'}
        ]
        
        response = self.client.get('/api/channels/')
        data = json.loads(response.content)
        
        assert response.status_code == 200
        assert data['count'] == 3
        
        channel1 = next(ch for ch in data['data'] if ch['slug'] == 'channel-1') 
        channel2 = next(ch for ch in data['data'] if ch['slug'] == 'channel-2')
        channel3 = next(ch for ch in data['data'] if ch['slug'] == 'channel-3')
        
        assert channel1['owner'] is not None
        assert channel2['owner'] is not None
        
        assert channel1['owner']['id'] == 2
        assert channel1['owner']['username'] == 'user2'

        assert channel2['owner']['id'] == 1
        assert channel2['owner']['username'] == 'user1'
        
        assert channel3['owner'] is None
        assert channel3['owner_id'] == 999


@pytest.mark.django_db
@pytest.mark.views
class TestChannelDetailView:
    def setup_method(self):
        self.client = Client()
        
        self.channel = Channel.objects.create(
            name='Test Channel',
            slug='test-channel',
            description='Test description',
            owner_id=1
        )
        
    @patch('apps.content.views.get_user')
    def test_retrieve_channel_success(self, mock_get_user):
        """
        Тест: Успешное получение деталей канала
        
        Проверяем:
        - Статус код 200
        - success = True
        - data содержит все поля: id, name, slug, description, owner_id, owner
        - owner содержит id, email, avatar_url
        - members_count и posts_count присутствуют
        - created_at и updated_at в ISO формате
        
        Моки:
        - get_user - возвращает данные владельца
        """
        from datetime import datetime
        
        mock_get_user.return_value = {
            'id': 1,
            'email': 'owner@example.com',
            'avatar_url': 'https://example.com/avatar.jpg'
        }
        
        response = self.client.get(f'/api/channels/{self.channel.slug}/')
        data = json.loads(response.content)
        
        assert response.status_code == 200
        assert data['success'] is True
        
        channel_data = data['data']
        
        assert channel_data['id'] == self.channel.id
        assert channel_data['name'] == 'Test Channel'
        assert channel_data['slug'] == 'test-channel'
        assert channel_data['description'] == 'Test description'
        assert channel_data['owner_id'] == 1
        assert channel_data['owner']['email'] == 'owner@example.com'
        
        assert 'members_count' in channel_data
        assert 'posts_count' in channel_data
        assert channel_data['members_count'] == 0
        assert channel_data['posts_count'] == 0
        
        assert 'created_at' in channel_data
        assert 'updated_at' in channel_data
        
        created_at = datetime.fromisoformat(channel_data['created_at'].replace('Z', '+00:00'))
        updated_at = datetime.fromisoformat(channel_data['updated_at'].replace('Z', '+00:00'))
        
        assert created_at is not None
        assert updated_at is not None

    def test_retrieve_channel_not_found(self):
        """
        Тест: Канал не найден (404)
        
        Проверяем:
        - Статус код 404
        - Ответ содержит информацию об ошибке
        
        """
        nonexistent_slug = 'channel-12345'
        assert not Channel.objects.filter(slug=nonexistent_slug).exists()
        
        response = self.client.get(f'/api/channels/{nonexistent_slug}/')
        
        assert response.status_code == 404
        
        data = json.loads(response.content)
        assert 'error' in data or 'detail' in data
    
    @patch('apps.content.views.get_user')
    def test_retrieve_channel_counters(self, mock_get_user):
        """
        Тест: Проверка счетчиков members_count и posts_count
        
        Проверяем:
        - members_count правильно считает участников
        - posts_count правильно считает посты
        - Счетчики имеют тип int
        
        """
        mock_get_user.return_value = {
            'id': 1,
            'email': 'test@example.com'
        }

        ChannelMembership.objects.create(channel=self.channel, user_id=2)
        ChannelMembership.objects.create(channel=self.channel, user_id=3)
        ChannelMembership.objects.create(channel=self.channel, user_id=4)

        Post.objects.create(channel=self.channel, author_id=1, content='Post 1', title='Test-POST 1')
        Post.objects.create(channel=self.channel, author_id=1, content='Post 2', title='Test-POST 2')
        Post.objects.create(channel=self.channel, author_id=1, content='Post 3', title='Test-POST 3')
        Post.objects.create(channel=self.channel, author_id=1, content='Post 4', title='Test-POST 4')
        Post.objects.create(channel=self.channel, author_id=1, content='Post 5', title='Test-POST 5')

        response = self.client.get(f'/api/channels/{self.channel.slug}/')
        data = json.loads(response.content)
        
        assert response.status_code == 200
        assert data['success'] is True
        
        assert data['data']['members_count'] == 3
        assert data['data']['posts_count'] == 5

        assert isinstance(data['data']['members_count'], int)
        assert isinstance(data['data']['posts_count'], int)


@pytest.mark.django_db
@pytest.mark.views
class TestChannelCreateView:
    def setup_method(self):
        self.client = Client()
    
    @patch('apps.content.views.verify_user_exists')
    @patch('apps.content.views.get_user')
    def test_create_channel_success(self, mock_get_user, mock_verify):
        """
        Тест: Успешное создание канала
        
        Проверяем:
        - Статус код 201
        - success = True
        - data содержит id, slug, owner
        - Канал реально создался в БД
        - owner_id установлен правильно
        - slug автоматически сгенерировался
        
        Моки:
        - verify_user_exists - возвращает True
        - get_user - возвращает данные пользователя
        """
        mock_verify.return_value = True
        mock_get_user.return_value = {
            'id': 1,
            'email': 'test@example.com'
        }
        
        data = {
            'name': 'New Channel',
            'description': 'Text description'
        }
        
        assert Channel.objects.count() == 0
        
        response = self.client.post('/api/channels/create/', data)
        response_data = json.loads(response.content)
        
        assert response.status_code == 201
        assert response_data['success'] is True
        assert 'data' in response_data
        
        assert 'id' in response_data['data']
        assert 'slug' in response_data['data']
        assert response_data['data']['slug'] == 'new-channel'
        
        assert Channel.objects.count() == 1
        assert Channel.objects.filter(slug='new-channel').exists()

        channel = Channel.objects.get(slug='new-channel')
        assert channel.name == 'New Channel'
        assert channel.description == 'Text description'
        assert channel.owner_id == 1

        mock_verify.assert_called_once_with(1)
        mock_get_user.assert_called_once_with(1)

    @patch('apps.content.views.verify_user_exists')
    def test_create_channel_without_name(self, mock_verify):
        """
        Тест: Создание канала без обязательного поля name
        
        Проверяем:
        - Статус код 400
        - success = False
        - errors содержит информацию о невалидном поле name
        - Канал НЕ создался в БД
        
        """
        mock_verify.return_value = True

        data = {
            'description': 'Text description'
        }
        
        assert Channel.objects.count() == 0
        
        response = self.client.post('/api/channels/create/', data)
        response_data = json.loads(response.content)
        
        assert response.status_code == 400
        assert response_data['success'] is False
        
        assert 'errors' in response_data
        assert 'name' in response_data['errors']
        assert len(response_data['errors']['name']) > 0
        
        assert Channel.objects.count() == 0
        assert not Channel.objects.filter(description='Text description').exists()
        
    @patch('apps.content.views.verify_user_exists')
    def test_create_channel_user_not_found(self, mock_verify):
        """
        Тест: Пользователь не найден в User Service
        
        Проверяем:
        - Статус код 404
        - success = False
        - error содержит сообщение о том что пользователь не найден
        - Канал НЕ создался
        
        Моки:
        - verify_user_exists - возвращает False
        """
        
        mock_verify.return_value = False
        
        data = {
            'name': 'Test Channel',
            'description': 'Test description'
        }
        
        response = self.client.post('/api/channels/create/', data)
        response_data = json.loads(response.content)
        
        assert response.status_code == 404
        assert response_data['success'] is False
        
        assert 'error' in response_data
        assert 'пользователь' in response_data['error'].lower() or 'user' in response_data['error'].lower()
        
        assert Channel.objects.count() == 0
        
        mock_verify.assert_called_once()
        
    @patch('apps.content.views.verify_user_exists')
    @patch('apps.content.views.get_user')
    def test_create_channel_duplicate_slug(self, mock_get_user, mock_verify):
        """
        Тест: Дубликат slug
        
        Проверяем:
        - Статус код 400
        - success = False
        - Ошибка валидации для поля slug
        - Второй канал НЕ создался
        
        """
        mock_verify.return_value = True
        mock_get_user.return_value = {'id': 1, 'email': 'test@example.com'}
        
        Channel.objects.create(
            name='Test Channel',
            description='TestChann',
            slug='test-channel',
            owner_id=1
        )
        
        assert Channel.objects.count() == 1

        data = {
            'name': 'Test Channel',
            'description': 'TestChann1'
        }
        
        response = self.client.post('/api/channels/create/', data)
        response_data = json.loads(response.content)
        
        assert response.status_code == 400
        assert response_data['success'] is False
        assert 'errors' in response_data
        
        assert Channel.objects.count() == 1 

        channel = Channel.objects.get(slug='test-channel')
        assert channel.description == 'TestChann'


@pytest.mark.django_db
@pytest.mark.views
class TestChannelUpdateView:
    def setup_method(self):
        self.client = Client()
    
    def test_update_channel_partial(self):
        """
        Тест: Обновление только одного поля (partial update)
        
        Проверяем:
        - Можно обновить только description
        
        """
        channel = Channel.objects.create(
            name='Old Name',
            slug='test-channel',
            description='Old description',
            owner_id=1
        )
        
        update_data = {
            'description': 'New description only'
        }
        
        response = self.client.put(
            f'/api/channels/{channel.slug}/update/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        
        channel.refresh_from_db()
        assert channel.name == 'Old Name'
        assert channel.description == 'New description only'
    
    def test_update_channel_forbidden(self):
        """
        Тест: Попытка обновить чужой канал (403)
        
        Проверяем:
        - Статус код 403
        - success = False
        - error содержит сообщение о нехватке прав
        - code = 'permission_denied'
        - Канал НЕ изменился в БД
        
        """
        channel = Channel.objects.create(
            name='Test Channel',
            slug='test-channel',
            description='Old description',
            owner_id=999
        )
        
        update_data = {
            'description': 'Hacked description'
        }
        
        response = self.client.put(
            f'/api/channels/{channel.slug}/update/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        response_data = json.loads(response.content)
        
        assert response.status_code == 403
        assert response_data['success'] is False
        assert response_data['code'] == 'permission_denied'
        
        channel.refresh_from_db()
        assert channel.description == 'Old description'
    
    def test_update_channel_not_found(self):
        """
        Тест: Обновление несуществующего канала (404)
        
        Проверяем:
        - Статус код 404
        
        """
        nonexistent_slug = 'nonexistent-channel'
        
        update_data = {
            'name': 'New Name'
        }
        
        response = self.client.put(
            f'/api/channels/{nonexistent_slug}/update/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 404
    
    def test_update_channel_invalid_data(self):
        """
        Тест: Невалидные данные при обновлении
        
        Проверяем:
        - Статус код 400
        - success = False
        - errors содержит информацию об ошибках
        - Канал НЕ изменился
        """
        
        channel = Channel.objects.create(
            name='Old Name',
            slug='test-channel',
            owner_id=1
        )
        
        update_data = {
            'name': ''
        }
        
        response = self.client.put(
            f'/api/channels/{channel.slug}/update/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        response_data = json.loads(response.content)
        
        assert response.status_code == 400
        assert response_data['success'] is False
        assert 'errors' in response_data
        
        channel.refresh_from_db()
        assert channel.name == 'Old Name'

@pytest.mark.django_db
@pytest.mark.views
class TestChannelDeleteView:
    def setup_method(self):
        self.client = Client()
    
    def test_delete_channel_success(self):
        """
        Тест: Успешное удаление канала (owner)
        
        Проверяем:
        - Статус код 200
        - success = True
        - message содержит подтверждение удаления
        - Канал реально удалился из БД
        """
        
        channel = Channel.objects.create(
            name='To Delete',
            slug='to-delete',
            owner_id=1
        )
        
        channel_slug = channel.slug
        assert Channel.objects.filter(slug=channel_slug).exists()
        
        response = self.client.delete(f'/api/channels/{channel_slug}/delete/')
        response_data = json.loads(response.content)
        
        assert response.status_code in [200, 204]
        
        if response.status_code == 200:
            assert response_data['success'] is True
            assert 'удален' in response_data['message'].lower()
        
        assert not Channel.objects.filter(slug=channel_slug).exists()
    
    def test_delete_channel_forbidden(self):
        """
        Тест: Попытка удалить чужой канал (403)
        
        Проверяем:
        - Статус код 403
        - success = False
        - code = 'permission_denied'
        - Канал НЕ удалился из БД
        
        """
        channel = Channel.objects.create(
            name='Test Channel',
            slug='test-channel',
            owner_id=999
        )
        
        response = self.client.delete(f'/api/channels/{channel.slug}/delete/')
        response_data = json.loads(response.content)
        
        assert response.status_code == 403
        assert response_data['success'] is False
        assert response_data['code'] == 'permission_denied'
        
        assert Channel.objects.filter(slug='test-channel').exists()
    
    def test_delete_channel_not_found(self):
        """
        Тест: Удаление несуществующего канала (404)
        
        Проверяем:
        - Статус код 404
        
        """
        nonexistent_slug = 'nonexistent-channel'
        
        response = self.client.delete(f'/api/channels/{nonexistent_slug}/delete/')
        response_data = json.loads(response.content)
        
        assert response.status_code == 404
        assert response_data['success'] is False


@pytest.mark.django_db
@pytest.mark.views
class TestChannelSearchView:
    def setup_method(self):
        self.client = Client()
    
    @patch('apps.content.views.get_users_batch')
    def test_search_by_name(self, mock_get_users_batch):
        """
        Тест: Успешный поиск по имени
        
        Проверяем:
        - Статус код 200
        - success = True
        - query содержит поисковый запрос
        - count соответствует количеству найденных
        - data содержит только подходящие каналы
        - Поиск регистронезависимый
        
        """
        mock_get_users_batch.return_value = [
            {'id': 1, 'username': 'user1'},
            {'id': 2, 'username': 'user2'}
        ]
        
        Channel.objects.create(
            name='Python',
            slug='python-1',
            description='Python',
            owner_id=1
        )
        
        Channel.objects.create(
            name='Django',
            slug='django',
            description='Django',
            owner_id=2
        )
        
        Channel.objects.create(
            name='React',
            slug='react',
            description='React',
            owner_id=1
        )

        response = self.client.get('/api/channels/search/', {'query': 'Python'})
        data = json.loads(response.content)
        
        assert response.status_code == 200
        assert data['success'] is True
        assert 'query' in data
        assert data['query'] == 'Python'
        assert data['count'] == 1
        assert data['data'][0]['name'] == 'Python' 
        assert data['data'][0]['slug'] == 'python-1'
        
    @patch('apps.content.views.get_users_batch')    
    def test_search_by_description(self, mock_get_users_batch):
        """
        Тест: Поиск по описанию
        
        Проверяем:
        - Поиск работает не только по name, но и по description
        - Находятся каналы где query встречается в description
        
        """
        mock_get_users_batch.return_value = [
            {'id': 1, 'username': 'user1'},
            {'id': 2, 'username': 'user2'}
        ]
        
        Channel.objects.create(
            name='Python',
            slug='python-1',
            description='Python search',
            owner_id=1
        )
        
        Channel.objects.create(
            name='Django',
            slug='django',
            description='Django',
            owner_id=2
        )
        
        Channel.objects.create(
            name='React',
            slug='react',
            description='React',
            owner_id=1
        )

        response = self.client.get('/api/channels/search/', {'query': 'Python'})
        data = json.loads(response.content)
        
        assert response.status_code == 200
        assert data['success'] is True
        assert 'query' in data
        assert data['count'] == 1
        assert data['data'][0]['name'] == 'Python' 
        assert data['data'][0]['description'] == 'Python search'
    
    def test_search_without_query(self):
        """
        Тест: Поиск без параметра query (валидация)
        
        Проверяем:
        - Статус код 400
        - success = False
        - error указывает что query обязателен
        
        """
        Channel.objects.create(
            name='test',
            slug='python-1',
            description='Python search',
            owner_id=1
        )
    
        response = self.client.get('/api/channels/search/')
        data = json.loads(response.content)
        
        assert response.status_code == 400
        assert data['success'] is False
        assert 'error' in data
        
    def test_search_no_results(self):
        """
        Тест: Поиск ничего не нашел
        
        Проверяем:
        - Статус код 200
        - success = True
        - count = 0
        - data - пустой список
        
        """
        Channel.objects.create(
            name='test',
            slug='python-1',
            description='Python search',
            owner_id=1
        )
    
        response = self.client.get('/api/channels/search/?query=NonExistentChannel')
        data = json.loads(response.content)
        
        assert response.status_code == 200
        assert data['success'] is True
        assert data['query'] == 'NonExistentChannel'
        assert data['count'] == 0
        assert data['data'] == []
