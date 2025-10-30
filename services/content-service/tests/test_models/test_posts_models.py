import pytest
import time
from django.db import IntegrityError, transaction
from apps.posts.models import Post
from apps.content.models import Channel


@pytest.mark.unit
@pytest.mark.models
class TestPostModel:
    def test_create_post_with_valid_data(self):
        channel = Channel.objects.create(
            name='TestChannel',
            description='TEST',
            owner_id=1
        )
        
        post = Post.objects.create(
            channel=channel,
            author_id=1,
            title='POST 1',
            slug='post-1',
            content='Content'
        )
        
        assert post.id is not None
        assert post.created_at is not None
        assert post.updated_at is not None
        assert post.title == 'POST 1'
        assert post.slug == 'post-1'
        assert post.content == 'Content'
        
        Post.objects.filter(id=post.id).exists()
        
    def test_slug_auto_generation(self):
        channel = Channel.objects.create(
            name='TestChannel',
            description='TEST',
            owner_id=1
        )
        
        post = Post.objects.create(
            channel=channel,
            author_id=1,
            title='POST 1',
            content='Content'
        )
        
        assert post.slug is not None
        assert post.slug == 'post-1'
        assert ' ' not in post.slug
        assert post.slug.islower()
        
    def test_title_unique(self):
        channel = Channel.objects.create(
            name='Test Channel',
            description='...',
            owner_id=1
        )

        Post.objects.create(
            channel=channel,
            title='UniquePOST',
            content='...',
            author_id=1
        )

        with pytest.raises(IntegrityError) as exc_info:
            with transaction.atomic():
                Post.objects.create(
                    channel=channel,
                    title='UniquePOST',
                    content='...',
                    author_id=2
                )

        error_message = str(exc_info.value).lower()
        assert 'unique constraint failed' in error_message or 'unique' in error_message

        assert Post.objects.filter(title='UniquePOST').count() == 1

        
    def test_channel_slug_unique_together(self):
        channel = Channel.objects.create(
            name='Channel',
            description='Test',
            owner_id=1
        )
        
        post1 = Post.objects.create(
            channel=channel,
            title='Post One',
            content='...',
            slug='post-one',
            author_id=1
        )
        
        with pytest.raises(IntegrityError):
            Post.objects.create(
                channel=channel,
                title='Post Two',
                content='...',
                slug='post-one',
                author_id=1
            )
        
    def test_channel_foreign_key(self):
        from django.db.models import ForeignKey
        
        channel = Channel.objects.create(
            name='Channel',
            description='Test',
            owner_id=1
        )
        
        post = Post.objects.create(
            channel=channel,
            title='Post Two',
            content='...',
            slug='post-one',
            author_id=1
        )

        field = Post._meta.get_field('channel')
        assert isinstance(field, ForeignKey)
        
        assert post.channel == channel
        assert isinstance(post.channel, Channel)
        
        assert post in channel.posts.all()
        assert hasattr(channel, 'posts')
        
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Post.objects.create(
                    title='Test no channel',
                    content='...',
                    slug='test-no-channel',
                    author_id=1
                )
            
        assert Post.objects.filter(title='Post Two', channel=channel).exists()
          
    def test_can_edit_by_author(self):
        channel = Channel.objects.create(
            name='Channel',
            description='Test',
            owner_id=1
        )
        
        post = Post.objects.create(
            channel=channel,
            title='Post Two',
            content='...',
            slug='post-one',
            author_id=1
        )
        
        assert post.can_edit(user_id=1, membership_role='member') is True
        assert post.can_edit(user_id=1, membership_role='moderator') is True
        assert post.can_edit(user_id=1, membership_role='something') is True
    
        
    def test_can_edit_by_owner(self):
        channel = Channel.objects.create(
            name='Channel',
            description='Test',
            owner_id=3
        )
        
        post = Post.objects.create(
            channel=channel,
            title='Post Two',
            content='...',
            slug='post-one',
            author_id=1
        )
        
        assert post.can_edit(user_id=3, membership_role='owner') is True
        assert post.can_edit(user_id=999, membership_role='owner') is True
        assert post.author_id != 999
    
    def test_can_edit_by_admin(self):
        channel = Channel.objects.create(
            name='Channel',
            description='Test',
            owner_id=3
        )
        
        post = Post.objects.create(
            channel=channel,
            title='Post Two',
            content='...',
            slug='post-one',
            author_id=1
        )
        
        
        assert post.can_edit(user_id=3, membership_role='admin') is True
        assert post.can_edit(user_id=999, membership_role='admin') is True
        assert post.author_id != 999
        
        
    def test_can_edit_by_member(self):
        channel = Channel.objects.create(
            name='Channel',
            description='Test',
            owner_id=3
        )
        
        post = Post.objects.create(
            channel=channel,
            title='Post Two',
            content='...',
            slug='post-one',
            author_id=1
        )
        
        assert post.can_edit(user_id=300, membership_role='member') is False
        assert post.can_edit(user_id=300, membership_role='moderator') is False
        assert post.author_id != 300
        
    
    def test_ordering(self):
        channel = Channel.objects.create(
            name='Channel',
            description='Test',
            owner_id=3
        )
        
        post1 = Post.objects.create(
            channel=channel,
            title='First Post',
            content='...',
            slug='first-post',
            author_id=1
        )
        
        time.sleep(0.01)
        post2 = Post.objects.create(
            channel=channel,
            title='Second Post',
            content='...',
            slug='second-post',
            author_id=1
        )
        
        time.sleep(0.01)
        post3 = Post.objects.create(
            channel=channel,
            title='Third Post',
            content='...',
            slug='third-post',
            author_id=1
        )
        
        posts = channel.posts.all()
        
        assert posts[0] == post3
        assert posts[1] == post2
        assert posts[2] == post1
        
        posts_list = list(posts)
        assert posts_list == [post3, post2, post1]
        
    def test_str_representation(self):
        channel = Channel.objects.create(
            name='Test Channel',
            slug='test',
            description='Desc',
            owner_id=1
        )

        post = Post.objects.create(
            title='My Post',
            content='Content here',
            slug='my-post',
            channel=channel,
            author_id=1
        )


        expected_str = f'{post.title} ({channel.slug})'
        assert str(post) == expected_str

        post_str = str(post)
        assert post.title in post_str
        assert channel.slug in post_str
