import pytest
import time
from django.db import IntegrityError, transaction
from apps.memberships.models import ChannelMembership
from apps.content.models import Channel


@pytest.mark.unit
@pytest.mark.models
class TestChannelMembershipModel:
    def test_create_membership_with_valid_data(self):
        channel = Channel.objects.create(
            name='Test Channel',
            description='Test',
            owner_id=1
        )
        
        membership = ChannelMembership.objects.create(
            channel=channel,
            user_id=1,
            role='owner'
        )
        
        assert membership.id is not None
        assert membership.channel is not None
        assert membership.user_id is not None
        assert membership.role is not None
        assert membership.joined_at is not None
        assert ChannelMembership.objects.filter(channel=channel).exists()
        
    def test_channel_foreign_key(self):
        channel = Channel.objects.create(
            name='Test Channel',
            description='Test',
            owner_id=1
        )
        
        membership = ChannelMembership.objects.create(
            channel=channel,
            user_id=1,
            role='owner'
        )
        
        assert membership.channel == channel
        assert membership in channel.memberships.all()
        assert isinstance(membership.channel, Channel)
        
        with pytest.raises(IntegrityError):
            membership = ChannelMembership.objects.create(
                channel=None,
                user_id=2,
                role='member'
            )
            
        
    def test_unique_channel_user_id(self):
        channel = Channel.objects.create(
            name='Test Channel',
            description='Test',
            owner_id=1
        )

        ChannelMembership.objects.create(
            channel=channel,
            user_id=1,
            role='member'
        )

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                ChannelMembership.objects.create(
                    channel=channel,
                    user_id=1,
                    role='owner'
                )

        another_channel = Channel.objects.create(
            name='Another Channel',
            description='Another test',
            owner_id=2
        )

        membership = ChannelMembership.objects.create(
            channel=another_channel,
            user_id=1,
            role='member'
        )

        assert membership.channel == another_channel
        assert ChannelMembership.objects.count() == 2
         
    def test_role_choices(self):
        channel = Channel.objects.create(
            name='Test Channel',
            description='Test',
            owner_id=1
        )

        member = ChannelMembership.objects.create(
            channel=channel,
            user_id=1,
            role='member'
        )
        
        moderator = ChannelMembership.objects.create(
            channel=channel,
            user_id=2,
            role='moderator'
        )
        
        admin = ChannelMembership.objects.create(
            channel=channel,
            user_id=3,
            role='admin'
        )
        
        owner = ChannelMembership.objects.create(
            channel=channel,
            user_id=4,
            role='owner'
        )
        
        assert member.role == 'member'
        assert moderator.role == 'moderator'
        assert admin.role == 'admin'
        assert owner.role == 'owner'
        
        assert ChannelMembership.objects.filter(role='member').exists()
        assert ChannelMembership.objects.filter(role='moderator').exists()
        assert ChannelMembership.objects.filter(role='admin').exists()
        assert ChannelMembership.objects.filter(role='owner').exists()
            
    def test_cascade_delete_when_channel_deleted(self):
        """Тест 5: Каскадное удаление при удалении канала"""
        channel = Channel.objects.create(
            name='Test Channel',
            description='Test',
            owner_id=1
        )
        
        membership1 = ChannelMembership.objects.create(
            channel=channel,
            user_id=1,
            role='owner'
        )
        
        membership2 = ChannelMembership.objects.create(
            channel=channel,
            user_id=2,
            role='member'
        )
        
        membership3 = ChannelMembership.objects.create(
            channel=channel,
            user_id=3,
            role='admin'
        )
        
        membership_ids = [membership1.id, membership2.id, membership3.id]
        channel.delete()
        
        assert not Channel.objects.filter(id=channel.id).exists()
        
        for membership_id in membership_ids:
            assert not ChannelMembership.objects.filter(id=membership_id).exists()
                
    def test_filter_by_role(self):
        """Тест 7: Фильтрация по role"""
        channel = Channel.objects.create(
            name='Test Channel',
            description='Test',
            owner_id=1
        )
        
        owner = ChannelMembership.objects.create(
            channel=channel,
            user_id=1,
            role='owner'
        )
        
        admin1 = ChannelMembership.objects.create(
            channel=channel,
            user_id=2,
            role='admin'
        )
        
        admin2 = ChannelMembership.objects.create(
            channel=channel,
            user_id=3,
            role='admin'
        )
        
        member1 = ChannelMembership.objects.create(
            channel=channel,
            user_id=4,
            role='member'
        )
        
        member2 = ChannelMembership.objects.create(
            channel=channel,
            user_id=5,
            role='member'
        )
        
        owners = ChannelMembership.objects.filter(channel=channel, role='owner')
        admins = ChannelMembership.objects.filter(channel=channel, role='admin')
        members = ChannelMembership.objects.filter(channel=channel, role='member')
        
        assert owners.count() == 1
        assert owner in owners
        
        assert admins.count() == 2
        assert admin1 in admins
        assert admin2 in admins
        
        assert members.count() == 2
        assert member1 in members
        assert member2 in members
    
    def test_ordering(self):
        """Тест 8: Проверка ordering (по joined_at)"""
        channel = Channel.objects.create(
            name='Test Channel',
            description='Test',
            owner_id=1
        )
        
        membership1 = ChannelMembership.objects.create(
            channel=channel,
            user_id=1,
            role='owner'
        )
        
        time.sleep(0.01)
        membership2 = ChannelMembership.objects.create(
            channel=channel,
            user_id=2,
            role='member'
        )
        
        time.sleep(0.01)
        membership3 = ChannelMembership.objects.create(
            channel=channel,
            user_id=3,
            role='member'
        )
        
        memberships_list = list(ChannelMembership.objects.all())
        assert memberships_list[0] == membership3
        assert memberships_list[1] == membership2
        assert memberships_list[2] == membership1
        assert memberships_list == [membership3, membership2, membership1]
    
    def test_str_representation(self):
        """Тест 9: Строковое представление __str__"""
        channel = Channel.objects.create(
            name='Test Channel',
            description='Test',
            owner_id=1
        )
        
        membership = ChannelMembership.objects.create(
            channel=channel,
            user_id=123,
            role='admin'
        )
        
        expected = f'123 - admin in {channel.name}'
        assert str(membership) == expected
        
        membership_str = str(membership)
        assert '123' in membership_str
        assert 'admin' in membership_str
        assert channel.name in membership_str
    
    def test_user_id_field(self):
        """Тест 10: Проверка поля user_id"""
        channel1 = Channel.objects.create(
            name='Channel 1',
            description='Test',
            owner_id=1
        )
        
        time.sleep(0.01)
        channel2 = Channel.objects.create(
            name='Channel 2',
            description='Test',
            owner_id=2
        )
        
        time.sleep(0.01)
        channel3 = Channel.objects.create(
            name='Channel 3',
            description='Test',
            owner_id=3
        )
        
        time.sleep(0.01)
        membership1 = ChannelMembership.objects.create(
            channel=channel1,
            user_id=100,
            role='member'
        )
        
        time.sleep(0.01)
        membership2 = ChannelMembership.objects.create(
            channel=channel2,
            user_id=100,
            role='admin'
        )
        
        time.sleep(0.01)
        membership3 = ChannelMembership.objects.create(
            channel=channel3,
            user_id=100,
            role='owner'
        )
        
        user_memberships = ChannelMembership.objects.filter(user_id=100)
        assert user_memberships.count() == 3
        assert membership1 in user_memberships
        assert membership2 in user_memberships
        assert membership3 in user_memberships


@pytest.mark.unit
@pytest.mark.models
class TestChannelMembershipBonuses:
    def test_count_members(self):
        """Тест 11: Подсчет участников канала"""
        channel = Channel.objects.create(
            name='Test Channel',
            description='Test',
            owner_id=1
        )
        
        assert channel.memberships.count() == 0
        
        ChannelMembership.objects.create(
            channel=channel,
            user_id=1,
            role='owner'
        )
        
        assert channel.memberships.count() == 1
        
        ChannelMembership.objects.create(
            channel=channel,
            user_id=2,
            role='member'
        )
        
        ChannelMembership.objects.create(
            channel=channel,
            user_id=3,
            role='admin'
        )
        
        assert channel.memberships.count() == 3
        
        membership_to_delete = ChannelMembership.objects.get(user_id=2)
        membership_to_delete.delete()
        
        assert channel.memberships.count() == 2
    
    def test_role_hierarchy(self):
        """Тест 12: Проверка иерархии ролей"""
        channel = Channel.objects.create(
            name='Test Channel',
            description='Test',
            owner_id=1
        )
        
        owner = ChannelMembership.objects.create(
            channel=channel,
            user_id=1,
            role='owner'
        )
        
        admin1 = ChannelMembership.objects.create(
            channel=channel,
            user_id=2,
            role='admin'
        )
        
        admin2 = ChannelMembership.objects.create(
            channel=channel,
            user_id=3,
            role='admin'
        )
        
        member1 = ChannelMembership.objects.create(
            channel=channel,
            user_id=4,
            role='member'
        )
        
        member2 = ChannelMembership.objects.create(
            channel=channel,
            user_id=5,
            role='member'
        )
        
        member3 = ChannelMembership.objects.create(
            channel=channel,
            user_id=6,
            role='member'
        )
        
        assert ChannelMembership.objects.filter(channel=channel, role='owner').count() == 1
        assert ChannelMembership.objects.filter(channel=channel, role='admin').count() == 2
        assert ChannelMembership.objects.filter(channel=channel, role='member').count() == 3
        
        assert owner.role == 'owner'
        assert admin1.role == 'admin'
        assert admin2.role == 'admin'
        assert member1.role == 'member'
        assert member2.role == 'member'
        assert member3.role == 'member'
    
    def test_update_role(self):
        """Тест 13: Изменение роли участника"""
        channel = Channel.objects.create(
            name='Test Channel',
            description='Test',
            owner_id=1
        )
        
        membership = ChannelMembership.objects.create(
            channel=channel,
            user_id=1,
            role='member'
        )
        
        assert membership.role == 'member'
        
        membership.role = 'moderator'
        membership.save()
        
        membership.refresh_from_db()
        assert membership.role == 'moderator'
        
        membership.role = 'admin'
        membership.save()
        
        membership.refresh_from_db()
        assert membership.role == 'admin'
        
        membership.role = 'member'
        membership.save()
        
        membership.refresh_from_db()
        assert membership.role == 'member'
    
    def test_get_owner(self):
        """Тест 14: Получение owner канала"""
        channel = Channel.objects.create(
            name='Test Channel',
            description='Test',
            owner_id=1
        )
        
        owner_membership = ChannelMembership.objects.create(
            channel=channel,
            user_id=100,
            role='owner'
        )
        
        ChannelMembership.objects.create(
            channel=channel,
            user_id=2,
            role='admin'
        )
        
        ChannelMembership.objects.create(
            channel=channel,
            user_id=3,
            role='member'
        )
        
        owner = ChannelMembership.objects.get(channel=channel, role='owner')
        
        assert owner == owner_membership
        assert owner.user_id == 100
        assert owner.role == 'owner'
    
    def test_user_channels_list(self):
        """Тест 15: Список всех каналов пользователя"""
        channel1 = Channel.objects.create(
            name='Channel 1',
            description='Test 1',
            owner_id=1
        )
        
        channel2 = Channel.objects.create(
            name='Channel 2',
            description='Test 2',
            owner_id=2
        )
        
        channel3 = Channel.objects.create(
            name='Channel 3',
            description='Test 3',
            owner_id=3
        )
        
        membership1 = ChannelMembership.objects.create(
            channel=channel1,
            user_id=100,
            role='member'
        )
        
        membership2 = ChannelMembership.objects.create(
            channel=channel2,
            user_id=100,
            role='admin'
        )
        
        membership3 = ChannelMembership.objects.create(
            channel=channel3,
            user_id=100,
            role='owner'
        )

        ChannelMembership.objects.create(
            channel=channel1,
            user_id=200,
            role='member'
        )
        
        user_memberships = ChannelMembership.objects.filter(user_id=100)
        
        assert user_memberships.count() == 3
        assert membership1 in user_memberships
        assert membership2 in user_memberships
        assert membership3 in user_memberships
        
        user_channels = [m.channel for m in user_memberships]
        
        assert len(user_channels) == 3
        assert channel1 in user_channels
        assert channel2 in user_channels
        assert channel3 in user_channels
