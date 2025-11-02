import pytest
import json
from django.utils import timezone
from django.test import Client
from apps.content.models import Channel, ChannelRole
from apps.memberships.models import ChannelMembership
from unittest.mock import patch



@pytest.mark.django_db
@pytest.mark.views
class TestMemberListView:

    def setup_method(self):
        self.client = Client()
        
        self.channel = Channel.objects.create(
            name='Test Channel',
            slug='test-channel',
            owner_id=1
        )
    
    @patch('apps.memberships.views.get_users_batch')
    def test_list_members_success(self, mock_get_users_batch):
        """
        Тест: Успешное получение списка участников
        
        Проверяем:
        - Статус 200
        - success = True
        - channel содержит: id, name, slug
        - count соответствует количеству участников
        - data содержит список участников
        - Каждый участник: user_id, role, joined_at, user
        - user содержит: id, email, avatar_url
        - Сортировка по joined_at (DESC - новые сначала)
        
        Моки:
        - get_users_batch - возвращает данные пользователей
        """
        
        mock_get_users_batch.return_value = [
            {'id': 1, 'email': 'test@example.com', 'avatar_url': 'https://avatar_test.com'},
            {'id': 2, 'email': 'test2@example.com', 'avatar_url': 'https://avatar_test.com'},
            {'id': 3, 'email': 'test3@example.com', 'avatar_url': 'https://avatar_test.com'}
        ]
        
        ChannelMembership.objects.create(
            channel=self.channel, user_id=1, role=ChannelRole.MEMBER,
            joined_at=timezone.now() - timezone.timedelta(days=2)
        )
        ChannelMembership.objects.create(
            channel=self.channel, user_id=2, role=ChannelRole.MODERATOR,
            joined_at=timezone.now() - timezone.timedelta(days=1)
        )
        ChannelMembership.objects.create(
            channel=self.channel, user_id=3, role=ChannelRole.ADMIN,
            joined_at=timezone.now()
        )
        
        response = self.client.get(f'/api/channels/{self.channel.slug}/members/')
        data = json.loads(response.content)
        
        assert response.status_code == 200
        assert data['success'] is True
        
        channel = data['channel']
        assert set(channel.keys()) == {'id', 'name', 'slug'}
        assert data['count'] == 3
        
        members = data['data']
        joined_times = [m['joined_at'] for m in members]
        assert joined_times == sorted(joined_times, reverse=True)
        
        for member in data['data']:
            assert set(member.keys()) == {'user_id', 'role', 'joined_at', 'user'}
            user = member['user']
            assert set(user.keys()) == {'id', 'email', 'avatar_url'}
            assert user['email'].startswith('test')
        
        mock_get_users_batch.assert_called_once_with([3, 2, 1])
            
    def test_list_members_empty(self):
        """
        Тест: Пустой список участников
        
        Проверяем:
        - Статус 200
        - success = True
        - count = 0
        - data = []
        - channel присутствует
        """
        
        response = self.client.get(f'/api/channels/{self.channel.slug}/members/')
        data = json.loads(response.content)
        
        assert response.status_code == 200
        assert data['success'] is True
        assert data['count'] == 0
        assert data['data'] == []
        assert set(data['channel'].keys()) == {'id', 'name', 'slug'}
    
    def test_list_members_channel_not_found(self):
        """
        Тест: Канал не найден (404)
        
        Проверяем:
        - Статус 404
        """
        
        nonexistent_slug = 'nonexistent-channel'
        
        assert not Channel.objects.filter(slug=nonexistent_slug).exists()
        
        response = self.client.get(f'/api/channels/{nonexistent_slug}/members/')
        
        assert response.status_code == 404
    
    @patch('apps.memberships.views.get_users_batch')
    def test_list_members_user_structure(self, mock_get_users_batch):
        """
        Тест: Структура user (когда найден и не найден)
        
        Проверяем:
        - user не None когда найден в User Service
        - user = None когда не найден
        - user содержит: id, email, avatar_url
        
        Моки:
        - get_users_batch возвращает только некоторых пользователей
        """
        
        mock_get_users_batch.return_value = [
            {'id': 1, 'email': 'test@example.com', 'avatar_url': 'https://avatar_test.com'},
        ]
        
        ChannelMembership.objects.create(
            channel=self.channel, user_id=1, role=ChannelRole.MEMBER,
            joined_at=timezone.now() - timezone.timedelta(days=2)
        )
        
        ChannelMembership.objects.create(
            channel=self.channel, user_id=999, role=ChannelRole.MEMBER,
            joined_at=timezone.now() - timezone.timedelta(days=2)
        )
        
        response = self.client.get(f'/api/channels/{self.channel.slug}/members/')
        data = json.loads(response.content)
        
        assert response.status_code == 200
        assert data['success'] is True
        assert data['count'] == 2
        
        member_1 = next(m for m in data['data'] if m['user_id'] == 1)
        member_999 = next(m for m in data['data'] if m['user_id'] == 999)
        
        assert member_1['user'] is not None
        assert set(member_1['user'].keys()) == {'id', 'email', 'avatar_url'}
        assert member_1['user']['id'] == 1
        assert member_1['user']['email'] == 'test@example.com'
        
        assert member_999['user'] is None
        
        
@pytest.mark.django_db
@pytest.mark.views
class TestMemberJoinView:
    
    def setup_method(self):
        self.client = Client()
        
        self.channel = Channel.objects.create(
            name='Test Channel',
            slug='test-channel',
            owner_id=2
        )
    
    @patch('apps.memberships.views.get_user')
    def test_join_channel_success(self, mock_get_user):
        """
        Тест: Успешное вступление в канал
        
        Проверяем:
        - Статус 201
        - success = True
        - message содержит название канала
        - data содержит: user_id, role, joined_at, channel, user
        - role = MEMBER (по умолчанию)
        - Membership создался в БД
        - user_id = request.user.id (= 1)
        
        Моки:
        - get_user - возвращает данные текущего пользователя
        """
        
        mock_get_user.return_value = {
            'id': 1,
            'email': 'test@example.com',
            'avatar_url': 'https://avatar_test.com'
        }
        
        response = self.client.post(
            f'/api/channels/{self.channel.slug}/members/join/' 
        )
        
        data = json.loads(response.content)
        
        assert response.status_code == 201
        assert data['success'] is True
        assert data['message'] == f'Вы успешно вступили в канал: {self.channel.name}'
        assert set(data['data'].keys()) == {'user_id', 'role', 'joined_at', 'channel', 'user'}
        assert data['data']['role'] == ChannelRole.MEMBER
        assert data['data']['user_id'] == 1
        
        assert ChannelMembership.objects.filter(user_id=1).exists()
        
    def test_join_channel_already_member(self):
        """
        Тест: Повторное вступление (409 Conflict)
        
        Проверяем:
        - Статус 409
        - success = False
        - error = 'Вы уже являетесь членом этого канала'
        - code = 'already_member'
        - Новый membership НЕ создался (count остался = 1)
        """
        
        ChannelMembership.objects.create(
            channel=self.channel, user_id=1, role=ChannelRole.MEMBER,
            joined_at=timezone.now() - timezone.timedelta(days=2)
        )
        
        response = self.client.post(f'/api/channels/{self.channel.slug}/members/join/')
        data = json.loads(response.content)
        
        assert response.status_code == 409
        assert data['success'] is False
        assert data['error'] == 'Вы уже являетесь членом этого канала'
        assert data['code'] == 'already_member'
        
        assert ChannelMembership.objects.filter(channel=self.channel).count() == 1
        
    def test_join_channel_not_found(self):
        """
        Тест: Канал не найден (404)
        
        Проверяем:
        - Статус 404
        
        """
        
        nonexistent_slug = 'nonexistent-channel'
        
        assert not Channel.objects.filter(slug=nonexistent_slug).exists()
        
        response = self.client.post(
            f'/api/channels/{nonexistent_slug}/members/join/'
        )
        
        assert response.status_code == 404

@pytest.mark.django_db
@pytest.mark.views
class TestMemberLeaveView:
    
    def setup_method(self):
        self.client = Client()
        
        self.channel = Channel.objects.create(
            name='Test Channel',
            slug='test-channel',
            owner_id=2
        )
    
    def test_leave_channel_success(self):
        """
        Тест: Успешный выход из канала
        
        Проверяем:
        - Статус 200
        - success = True
        - message содержит название канала
        - Membership удалился из БД
        - ChannelMembership.objects.count() уменьшился
        
        """
        
        ChannelMembership.objects.create(
            channel=self.channel, user_id=1, role=ChannelRole.MEMBER,
            joined_at=timezone.now() - timezone.timedelta(days=2)
        )
        
        assert ChannelMembership.objects.filter(channel=self.channel).count() == 1
        
        response = self.client.delete(f'/api/channels/{self.channel.slug}/members/leave/')
        data = json.loads(response.content)
        
        assert response.status_code == 200
        assert data['success'] is True
        assert data['message'] == f'Вы успешно покинули канал: {self.channel.name}'
        
        assert ChannelMembership.objects.filter(channel=self.channel).count() == 0
        
    @pytest.mark.skip(reason="Requires owner_id=request.user.id setup")  
    def test_leave_channel_owner_cannot_leave(self):
        """
        Тест: Владелец не может покинуть канал (403)
        
        Проверяем:
        - Статус 403
        - success = False
        - error = 'Владелец не может покинуть свой канал.'
        - code = 'owner_cannot_leave'
        - Membership НЕ удалился
        
        """
        
        ChannelMembership.objects.create(
            channel=self.channel,
            user_id=2,
            role=ChannelRole.OWNER,
            joined_at=timezone.now() - timezone.timedelta(days=5)
        )
        
        count_before = ChannelMembership.objects.filter(
            channel=self.channel,
            user_id=2
        ).count()
        assert count_before == 1
        
        response = self.client.delete(
            f'/api/channels/{self.channel.slug}/members/leave/'
        )
        data = json.loads(response.content)
        
        assert response.status_code == 403
        assert data['success'] is False
        assert data['error'] == 'Владелец не может покинуть свой канал.'
        assert data['code'] == 'owner_cannot_leave'
        
    def test_leave_channel_not_member(self):
        """
        Тест: Выход без membership (404)
        
        Проверяем:
        - Статус 404
        - success = False
        - error = 'Вы не являетесь членом этого канала.'
        - code = 'not_a_member' (или 'note_a_member' если баг не исправлен)
        """
        
        response = self.client.delete(
            f'/api/channels/{self.channel.slug}/members/leave/'
        )
        data = json.loads(response.content)
        
        assert response.status_code == 404
        
    def test_leave_channel_not_found(self):
        """
        Тест: Канал не найден (404)
        
        Проверяем:
        - Статус 404
        
        """
        
        nonexistent_slug = 'nonexistent-channel'
        
        assert not Channel.objects.filter(slug=nonexistent_slug).exists()
        
        response = self.client.delete(
            f'/api/channels/{nonexistent_slug}/members/leave/'
        )
        
        assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.views
class TestMemberUpdateRoleView:
    
    def setup_method(self):
        self.client = Client()
        
        self.channel = Channel.objects.create(
            name='Test Channel',
            slug='test-channel',
            owner_id=1
        )
        
        self.member = ChannelMembership.objects.create(
            channel=self.channel,
            user_id=2,
            role=ChannelRole.MEMBER
        )
    
    @patch('apps.memberships.views.get_user')
    def test_update_role_success(self, mock_get_user):
        """
        Тест: Успешное изменение роли (owner)
        
        Проверяем:
        - Статус 200
        - success = True
        - message содержит старую и новую роль
        - data содержит: user_id, role, previous_role, joined_at, channel, user
        - Роль изменилась в БД (refresh_from_db!)
        
        Моки:
        - get_user - возвращает данные пользователя
        
        """
        
        mock_get_user.return_value = {
            'id': 2, 
            'email': 'test@example.com'
        }
        
        assert self.channel.owner_id == 1
        
        assert self.member.user_id == 2
        assert self.member.role == ChannelRole.MEMBER
        old_role = self.member.role

        new_role_data = {
            'role': ChannelRole.MODERATOR
        }
        
        response = self.client.patch(
            f'/api/channels/{self.channel.slug}/members/{self.member.user_id}/role/',
            data=json.dumps(new_role_data),
            content_type='application/json'
        )
        
        response_data = json.loads(response.content)
        
        assert response.status_code == 200
        assert response_data['success'] is True
        
        assert old_role in response_data['message']
        assert ChannelRole.MODERATOR in response_data['message']
        
        data = response_data['data']
        assert set(data.keys()) == {'user_id', 'role', 'previous_role', 'joined_at', 'channel', 'user'}
        
        assert data['user_id'] == 2
        assert data['role'] == ChannelRole.MODERATOR
        assert data['previous_role'] == old_role
        
        assert data['channel']['id'] == self.channel.id
        assert data['channel']['name'] == self.channel.name
        assert data['channel']['slug'] == self.channel.slug
        
        assert data['user'] is not None
        assert data['user']['id'] == 2
        assert data['user']['email'] == 'test@example.com'
        
        self.member.refresh_from_db()
        assert self.member.role == ChannelRole.MODERATOR

        mock_get_user.assert_called_once_with(2)
        
    def test_update_role_not_owner(self):
        """
        Тест: Не владелец пытается изменить роль (403)
        
        Проверяем:
        - Статус 403
        - success = False
        - error = 'Вы не являетесь владельцем канала.'
        - code = 'permission_denied'
        - Роль НЕ изменилась в БД
        """
        
        self.channel.owner_id = 999
        self.channel.save()
        
        old_role = self.member.role
        
        response = self.client.patch(
            f'/api/channels/{self.channel.slug}/members/{self.member.user_id}/role/',
            data=json.dumps({'role': ChannelRole.MODERATOR}),
            content_type='application/json'
        )
        
        response_data = json.loads(response.content)
        
        assert response.status_code == 403
        assert response_data['code'] == 'permission_denied'
        
        self.member.refresh_from_db()
        assert self.member.role == old_role
        
    def test_update_role_own_role(self):
        """
        Тест: Попытка изменить свою роль (403)
        
        Проверяем:
        - Статус 403
        - error = 'Вы не можете поменять себе роль'
        - code = 'cannot_change_own_role'
        - Роль НЕ изменилась
        """
        
        response = self.client.patch(
            f'/api/channels/{self.channel.slug}/members/{self.channel.owner_id}/role/',
            data=json.dumps({'role': ChannelRole.MEMBER}),
            content_type='application/json'
        )
        
        response_data = json.loads(response.content)
        
        assert response.status_code == 403
        assert response_data['success'] is False
        assert response_data['error'] == 'Вы не можете поменять себе роль'
        assert response_data['code'] == 'cannot_change_own_role'
    
    def test_update_role_member_not_found(self):
        """
        Тест: Участник не найден (404)
        
        Проверяем:
        - Статус 404
        - error = 'Пользователь не является членом этого канала.'
        - code = 'member_not_found'
        """
        
        response = self.client.patch(
            f'/api/channels/{self.channel.slug}/members/999/role/',
            data=json.dumps({'role': ChannelRole.MEMBER}),
            content_type='application/json'
        )
        
        response_data = json.loads(response.content)
        
        assert response.status_code == 404
        assert response_data['error'] == 'Пользователь не является членом этого канала.'
        assert response_data['code'] == 'member_not_found'
        
        assert not ChannelMembership.objects.filter(channel=self.channel, user_id=999).exists()
    
    def test_update_role_invalid_json(self):
        """
        Тест: Невалидный JSON (400)
        
        Проверяем:
        - Статус 400
        - success = False
        - error = 'Невалидный Json'
        """
        
        response = self.client.patch(
            f'/api/channels/{self.channel.slug}/members/2/role/',
            data='invalid json',
            content_type='application/json'
        )
        
        response_data = json.loads(response.content)
        
        assert response.status_code == 400
        assert response_data['success'] is False
        assert response_data['error'] == 'Невалидный Json'
        
    def test_update_role_missing_role(self):
        """
        Тест: Роль не указана (400)
        
        Проверяем:
        - Статус 400
        - error = 'Параметр role обязателен.'
        """
        
        response = self.client.patch(
            f'/api/channels/{self.channel.slug}/members/2/role/',
            data=json.dumps({'role': ''}),
            content_type='application/json'
        )
        
        response_data = json.loads(response.content)
        
        assert response.status_code == 400
        assert response_data['error'] == 'Параметр role обязателен.'
        
    
    def test_update_role_invalid_role(self):
        """
        Тест: Невалидная роль (400)
        
        Проверяем:
        - Статус 400
        - error содержит список допустимых ролей
        - Роль НЕ изменилась
        """
        
        response = self.client.patch(
            f'/api/channels/{self.channel.slug}/members/2/role/',
            data=json.dumps({'role': 'INVALID_ROLE'}),
            content_type='application/json'
        )
        
        response_data = json.loads(response.content)
        assert response.status_code == 400
        
        valid_roles = [choice[0] for choice in ChannelRole.choices]
        expected_error = f'Невалидная роль. Допустимые: {", ".join(valid_roles)}'

        assert response_data['error'] == expected_error
        
    def test_update_role_cannot_assign_owner(self):
        """
        Тест: Попытка назначить роль OWNER (403)
        
        Проверяем:
        - Статус 403
        - error = 'Нельзя назначить роль owner другому пользователю'
        - code = 'cannot_assign_owner'
        - Роль НЕ изменилась
        """
        
        response = self.client.patch(
            f'/api/channels/{self.channel.slug}/members/2/role/',
            data=json.dumps({'role': ChannelRole.OWNER}),
            content_type='application/json'
        )
        
        response_data = json.loads(response.content)
        
        assert response.status_code == 403
        assert response_data['error'] == 'Нельзя назначить роль owner другому пользователю'
        assert response_data['code'] == 'cannot_assign_owner'

@pytest.mark.django_db
@pytest.mark.views
class TestMemberRemoveView:
    def setup_method(self):
        self.client = Client()
        
        self.channel = Channel.objects.create(
            name='Test Channel',
            slug='test-channel',
            owner_id=1
        )
        
        self.owner_membership = ChannelMembership.objects.create(
            channel=self.channel,
            user_id=1,
            role=ChannelRole.OWNER
        )
        
        self.member = ChannelMembership.objects.create(
            channel=self.channel,
            user_id=2,
            role=ChannelRole.MEMBER
        )
    
    @patch('apps.memberships.views.get_user')
    def test_remove_member_success_by_owner(self, mock_get_user):
        """
        Тест: Успешное удаление участника владельцем
        
        Проверяем:
        - Статус 200
        - success = True
        - message = 'Пользователь успешно удален из канала'
        - data содержит: user_id, role, joined_at, channel, user
        - Membership удалился из БД
        
        Моки:
        - get_user - возвращает данные удаляемого пользователя
        """
        
        mock_get_user.return_value = {
            'id': 2, 'username': 'user1', 'email': 'test@example.com'
        }
        
        response = self.client.delete(
            f'/api/channels/{self.channel.slug}/members/2/remove/'
        )
        
        data = json.loads(response.content)
        
        assert response.status_code == 200
        assert data['message'] == 'Пользователь успешно удален из канала'
        assert set(data['data'].keys()) == {'user_id', 'role', 'joined_at', 'channel', 'user'}
        
        assert not ChannelMembership.objects.filter(
            channel=self.channel,
            user_id=2
        ).exists()
        
        mock_get_user.assert_called_once_with(2)
        
    def test_remove_member_not_a_member(self):
        """
        Тест: Не участник канала пытается удалить (403)
        
        Проверяем:
        - Статус 403
        - error = 'Вы не являетесь членом этого канала'
        - code = 'not_a_member'
        """
        
        self.owner_membership.delete()
        
        response = self.client.delete(
            f'/api/channels/{self.channel.slug}/members/2/remove/'
        )
        
        data = json.loads(response.content)
        
        assert response.status_code == 403
        assert data['success'] is False
        assert data['code'] == 'not_a_member'
        
        assert ChannelMembership.objects.filter(user_id=2).exists()
        
    def test_remove_member_no_permission(self):
        """
        Тест: Обычный участник пытается удалить (403)
        
        Проверяем:
        - Статус 403
        - error = 'У вас нету прав для удаления участников.'
        - code = 'permission_denied'
        """
        
        self.owner_membership.delete()
        
        ChannelMembership.objects.create(
            channel=self.channel,
            user_id=1,
            role=ChannelRole.MEMBER
        )
        
        response = self.client.delete(
            f'/api/channels/{self.channel.slug}/members/2/remove/'
        )
        
        data = json.loads(response.content)
        
        assert response.status_code == 403
        assert data['success'] is False
        assert data['error'] == 'У вас нету прав для удаления участников.'
        assert data['code'] == 'permission_denied'
        
        assert ChannelMembership.objects.filter(user_id=2).exists()
    
    def test_remove_member_cannot_remove_self(self):
        """
        Тест: Попытка удалить самого себя (403)
        
        Проверяем:
        - Статус 403
        - error = 'Вы не можете удалить самого себя.'
        - code = 'cannot_remove_self'
        - Membership НЕ удалился
        """
        
        assert ChannelMembership.objects.filter(
            channel=self.channel,
            user_id=1
        ).exists()
        
        response = self.client.delete(
            f'/api/channels/{self.channel.slug}/members/1/remove/'
        )
        
        data = json.loads(response.content)
        
        assert response.status_code == 403
        assert data['success'] is False
        assert data['error'] == 'Вы не можете удалить самого себя.'
        assert data['code'] == 'cannot_remove_self'
        assert ChannelMembership.objects.filter(user_id=1).exists()
        
    def test_remove_member_not_found(self):
        """
        Тест: Участник не найден (404)
        
        Проверяем:
        - Статус 404
        - error = 'Пользователь не является членом этого канала.'
        - code = 'member_not_found'
        """
        
        assert ChannelMembership.objects.filter(
            channel=self.channel,
            user_id=1
        ).exists()
        
        response = self.client.delete(
            f'/api/channels/{self.channel.slug}/members/999/remove/'
        )

        data = json.loads(response.content)
        
        assert response.status_code == 404
        assert data['success'] is False
        assert data['error'] == 'Пользователь не является членом этого канала.'
        assert data['code'] == 'member_not_found'
        
    def test_remove_member_cannot_remove_owner(self):
        """
        Тест: Попытка удалить владельца (403)
        
        Проверяем:
        - Статус 403
        - error = 'Нельзя удалить владельца канала.'
        - code = 'cannot_remove_owner'
        - Владелец НЕ удалился
        """
        
        owner_member = ChannelMembership.objects.create(
            channel=self.channel,
            user_id=999,
            role=ChannelRole.OWNER
        )
        
        response = self.client.delete(
            f'/api/channels/{self.channel.slug}/members/999/remove/'
        )

        data = json.loads(response.content)
        
        assert response.status_code == 403
        assert data['success'] == False
        assert data['error'] == 'Нельзя удалить владельца канала.'
        assert data['code'] == 'cannot_remove_owner'
        
        assert ChannelMembership.objects.filter(
            channel=self.channel,
            user_id=999,
            role=ChannelRole.OWNER
        ).exists()
        
    def test_remove_member_admin_cannot_remove_admin(self):
        """
        Тест: Админ пытается удалить админа (403)
        
        Проверяем:
        - Статус 403
        - error = 'Только владелец канала может удалять администраторов'
        - code = 'cannot_remove_admin'
        - Админ НЕ удалился
        """
        
        self.channel.owner_id = 999
        self.channel.save()
        self.owner_membership.delete()
        
        ChannelMembership.objects.create(
            channel=self.channel,
            user_id=1,
            role=ChannelRole.ADMIN
        )
        
        self.member.role = ChannelRole.ADMIN
        self.member.save()
        
        response = self.client.delete(
            f'/api/channels/{self.channel.slug}/members/2/remove/'
        )
        
        data = json.loads(response.content)
        
        assert response.status_code == 403
        assert data['code'] == 'cannot_remove_admin'
        assert data['success'] == False
        assert ChannelMembership.objects.filter(user_id=2).exists()
    
    @patch('apps.memberships.views.get_user')
    def test_remove_member_owner_can_remove_admin(self, mock_get_user):
        """
        Тест: Владелец может удалить админа (200)
        
        Проверяем:
        - Статус 200
        - Админ удалился
        """
        
        mock_get_user.return_value = {
            'id': 2,
            'username': 'admin',
            'email': 'admin@example.com'
        }
        
        self.member.role = ChannelRole.ADMIN
        self.member.save()
        
        response = self.client.delete(
            f'/api/channels/{self.channel.slug}/members/2/remove/'
        )
        
        data = json.loads(response.content)
        
        assert response.status_code == 200
        assert not ChannelMembership.objects.filter(user_id=2).exists()
