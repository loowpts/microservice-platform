import pytest
import time
from django.db import IntegrityError, transaction
from apps.content.models import Channel
from apps.posts.models import Post
from apps.memberships.models import ChannelMembership


@pytest.mark.unit
@pytest.mark.models
class TestChannelModel:
    def test_create_channel_with_valid_data(self):
        channel = Channel.objects.create(
            name='Test Channel',
            description='TEST',
            owner_id=1
        )
        
        assert channel.id is not None
        assert channel.name == 'Test Channel'
        assert channel.description == 'TEST'
        assert channel.owner_id == 1
        
        assert channel.created_at is not None
        assert channel.updated_at is not None
        
        assert Channel.objects.filter(name='Test Channel').exists()
        assert Channel.objects.count() == 1
        
    def test_slug_auto_generation_from_name(self):
        channel = Channel.objects.create(
            name='My Test Channel',
            description='TEST',
            owner_id=1
        )    
        
        assert channel.slug is not None
        assert channel.slug == 'my-test-channel'
        assert ' ' not in channel.slug
        assert channel.slug.islower()
        
    def test_slug_generation_with_special_characters(self):
        channel = Channel.objects.create(
            name='Channel!@#$%^&*()',
            description='TEST',
            owner_id=1
        ) 
    
        assert channel.slug == 'channel'        

    def test_channel_name_must_be_unique(self):
        Channel.objects.create(name='Unique Channel', description='...', owner_id=1)
        
        with pytest.raises(IntegrityError) as exc_info:
            with transaction.atomic():
                Channel.objects.create(name='Unique Channel', description='...', owner_id=2)
        
        error_message = str(exc_info.value).lower()
        assert 'unique constraint failed' in error_message or 'unique' in error_message
        
        assert Channel.objects.filter(name='Unique Channel').count() == 1

    def test_channel_slug_must_be_unique(self):
        channel1 = Channel.objects.create(
            name='Channel One',
            slug='test-channel',
            description='First',
            owner_id=1
        )
        
        with pytest.raises(IntegrityError):
            Channel.objects.create(
                name='Channel Two',
                slug='test-channel',
                description='Second',
                owner_id=1
            )
    
    def test_channels_ordered_by_created_at_desc(self):
        channel1 = Channel.objects.create(
            name='First Channel',
            description='Created first',
            owner_id=1
        )
        time.sleep(0.01)
        channel2 = Channel.objects.create(
            name='Second Channel',
            description='Created second',
            owner_id=1
        )
        time.sleep(0.01)
        channel3 = Channel.objects.create(
            name='Third Channel',
            description='Created third',
            owner_id=1
        )
        
        channels = Channel.objects.all()
        
        assert channels[0] == channel3
        assert channels[1] == channel2
        assert channels[2] == channel1

        channels_list = list(channels)
        assert channels_list == [channel3, channel2, channel1]
        
    def test_channel_str_representation(self):
        channel = Channel.objects.create(
            name='TestChannel',
            description='TEST',
            owner_id=1
        )
        
        assert str(channel) == 'TestChannel'

    def test_channel_has_owner_id(self):
        channel1 = Channel.objects.create(
            name='FirstChannel',
            description='TEST',
            owner_id=100
        )
        
        channel2 = Channel.objects.create(
            name='SecondChannel',
            description='TEST',
            owner_id=200
        )
        
        assert channel1.owner_id == 100
        assert channel2.owner_id == 200
        
        owner1_channel = Channel.objects.filter(owner_id=100)
        assert owner1_channel.count() == 1
        assert owner1_channel.first() == channel1
        
        owner2_channel = Channel.objects.filter(owner_id=200)
        assert owner2_channel.count() == 1
        assert owner2_channel.first() == channel2

    def test_cascade_delete_posts_when_channel_deleted(self):
        channel = Channel.objects.create(
            name='Channel To Delete',
            description='Test',
            owner_id=1
        )
        
        post1 = Post(
            channel=channel,
            author_id=1,
            title='Post 1',
            slug='post-1',
            content='Content 1'
        )
        post1.save()
    
        post2 = Post(
            channel=channel,
            author_id=1,
            title='Post 2',
            slug='post-2',
            content='Content 2'
        )
        post2.save()
        
        post3 = Post(
            channel=channel,
            author_id=1,
            title='Post 3',
            slug='post-3',
            content='Content 3'
        )
        post3.save()
        
        posts_count = Post.objects.filter(channel=channel).count()
        assert posts_count == 3
        assert Post.objects.count() == 3
    
        post_ids = [post1.id, post2.id, post3.id]
        
        channel.delete()
    
        assert not Channel.objects.filter(id=channel.id).exists()
        assert Post.objects.count() == 0
        
        for post_id in post_ids:
            assert not Post.objects.filter(id=post_id).exists()

    def test_cascade_delete_memberships_when_channel_deleted(self):
        channel = Channel.objects.create(
            name='TestChannel',
            description='Test',
            owner_id=1
        )

        membership1 = ChannelMembership.objects.create(
            channel=channel,
            user_id=10,
            role='member'
        )
        
        membership2 = ChannelMembership.objects.create(
            channel=channel,
            user_id=20,
            role='admin'
        )
        
        membership3 = ChannelMembership.objects.create(
            channel=channel,
            user_id=30,
            role='member'
        )
        
        assert ChannelMembership.objects.filter(channel=channel).count() == 3
        assert ChannelMembership.objects.count() == 3
        
        memberships_ids = [membership1.id, membership2.id, membership3.id]
        
        channel.delete()
        
        assert not Channel.objects.filter(id=channel.id).exists()
        assert ChannelMembership.objects.count() == 0
        
        for membership_id in memberships_ids:
            assert not ChannelMembership.objects.filter(id=membership_id).exists()
        
    def test_full_cascade_delete(self):
        channel = Channel.objects.create(
            name='FullChannel',
            description='Test',
            owner_id=1
        )

        Post.objects.create(
            channel=channel,
            author_id=1,
            title='POST1',
            slug='post-1',
            content='Content'
        )

        Post.objects.create(
            channel=channel,
            author_id=1,
            title='POST2',
            slug='post-2',
            content='Content'
        )

        ChannelMembership.objects.create(channel=channel, user_id=10, role='member')
        ChannelMembership.objects.create(channel=channel, user_id=20, role='admin')

        assert Post.objects.filter(channel=channel).count() == 2
        assert ChannelMembership.objects.filter(channel=channel).count() == 2

        channel.delete()

        assert Post.objects.count() == 0
        assert ChannelMembership.objects.count() == 0
        assert Channel.objects.count() == 0

        
        
