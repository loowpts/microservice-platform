import pytest
import json
from django.test import Client
from apps.content.models import Channel
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
        
    @patch('apps.content.views.get_user')
    def test_channel_detail(self, mock_get_user):
        """
        Тест 2: GET /api/channels/{slug}/ - детали канала
        
        Проверяем:
        - Статус код 200
        - success = True
        - Все поля канала присутствуют
        - Счетчики members_count и posts_count работают
        """
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
        
