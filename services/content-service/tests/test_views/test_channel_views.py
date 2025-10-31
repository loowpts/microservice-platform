import pytest
import json
from django.test import Client
from apps.content.models import Channel
from apps.posts.models import Post
from apps.memberships.models import ChannelMembership
from unittest.mock import patch


@pytest.mark.django_db
@pytest.mark.views
class TestChannelViews:
    def setup_method(self):
        self.client = Client()
        
        self.channel = Channel.objects.create(
            name='Test Channel',
            slug='test-channel',
            description='Test description',
            owner_id=1
        )
    
    @patch('apps.content.views.get_users_batch')
    def test_channel_list(self, mock_get_users_batch):
        """
        Тест 1: GET /api/channels/ - список каналов
        
        Проверяем:
        - Статус код 200
        - success = True
        - Возвращается список каналов в 'data'
        - Данные канала корректны
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
    
    @patch('apps.content.views.get_users_batch')
    def test_list_channels_empty(self, mock_get_users_batch):
        Channel.objects.all().delete()
        
        response = self.client.get('/api/channels/')
        data = json.loads(response.content)
        
        assert response.status_code == 200
        assert data['success'] is True
        assert data['data'] == []
        assert data['count'] == 0
        
        mock_get_users_batch.assert_not_called()
    
    @patch('apps.content.views.get_users_batch')
    def test_list_multiple_channels(self, mock_get_users_batch):
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
        assert 'test4' in  slugs
        
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
    def test_channel_detail(self, mock_get_user):
        mock_get_user.return_value = {
            'id': 1,
            'email': 'owner@example.com',
            'avatar_url': 'https://example.com/avatar.jpg'
        }
        
        response = self.client.get(f'/api/channels/{self.channel.slug}/')
        
        data = json.loads(response.content)
        
        assert response.status_code == 200
        assert data['success'] is True
        assert 'data' in data
        
        channel_data = data['data']
        
        assert channel_data['id'] == self.channel.id
        assert channel_data['name'] == 'Test Channel'
        assert channel_data['slug'] == 'test-channel'
        assert channel_data['description'] == 'Test description'
        assert channel_data['owner_id'] == 1
        
        assert 'owner' in channel_data
        assert channel_data['owner']['id'] == 1
        assert channel_data['owner']['email'] == 'owner@example.com'
        
        assert 'members_count' in channel_data
        assert 'posts_count' in channel_data
        assert channel_data['members_count'] == 0
        assert channel_data['posts_count'] == 0
        
        assert 'created_at' in channel_data
        assert 'updated_at' in channel_data
    
    @patch('apps.content.views.get_user') 
    def test_retrieve_channel_success(self, mock_get_user):
        from datetime import datetime
        mock_get_user.return_value = {
            'id': 1,
            'email': 'owner@example.com',
            'avatar_url': 'https://example.com/avatar.jpg'
        }
        
        response = self.client.get(f'/api/channels/{self.channel.slug}/')
        data = json.loads(response.content)
        
        assert response.status_code == 200
        assert data['success'] == True

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
        nonexistent_slug = 'channel-12345'
        assert not Channel.objects.filter(slug=nonexistent_slug).exists()
        
        response = self.client.get(f'/api/channels/{nonexistent_slug}/')
        
        assert response.status_code == 404
        
        data = json.loads(response.content)
        assert 'error' in data or 'detail' in data
    
    @patch('apps.content.views.get_user')
    def test_retrieve_channel_counter(self, mock_get_user):
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
        assert data['success'] == True
        
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
        assert response_data['success'] == True
        assert 'data' in response_data
        
        assert 'id' in response_data['data']
        assert 'slug' in response_data['data']
        assert response_data['data']['slug'] == 'new-channel'
        
        assert Channel.objects.count() == 1
        assert Channel.objects.filter(slug='new-channel')

        channel = Channel.objects.get(slug='new-channel')
        assert channel.name == 'New Channel'
        assert channel.description == 'Text description'
        assert channel.owner_id == 1

        mock_verify.assert_called_once_with(1)
        mock_get_user.assert_called_once_with(1)
