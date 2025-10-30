import pytest
import time
from django.db import IntegrityError, transaction
from apps.comments.models import Comment
from apps.posts.models import Post
from apps.content.models import Channel


@pytest.mark.unit
@pytest.mark.models
class TestCommentModel:
    def test_create_comment_with_valid_data(self):
        channel = Channel.objects.create(
            name='TestChannel',
            description='TestChannel',
            owner_id=1
        )
        
        post = Post.objects.create(
            title='My Post',
            content='Content here',
            slug='my-post',
            channel=channel,
            author_id=1
        )
        
        comment = Comment.objects.create(
            post=post,
            author_id=33,
            content='Text comment test'
        )
        
        assert comment.id is not None
        assert comment.author_id == 33
        assert comment.content == 'Text comment test'
        assert comment.created_at is not None
        assert comment.parent == None
        assert Comment.objects.filter(id=comment.id).exists()
        
    
    def test_post_foreign_key(self):
        """Тест 2: Проверка связи с Post (ForeignKey)"""
        channel = Channel.objects.create(
            name='TestChannel',
            description='TestChannel',
            owner_id=1
        )
        
        post = Post.objects.create(
            title='My Post',
            content='Content here',
            slug='my-post',
            channel=channel,
            author_id=1
        )
        
        parent_comment = Comment.objects.create(
            post=post,
            author_id=33,
            content='Parent comment'
        )
        
        reply = Comment.objects.create(
            post=post,
            author_id=44,
            content='Child comment',
            parent=parent_comment
        )
        
        assert reply.id is not None
        assert reply.parent == parent_comment
        assert reply.parent.id == parent_comment.id
        assert reply in parent_comment.replies.all()
        assert reply.post == post
        assert reply.content == 'Child comment'
                
    def test_create_nested_comment(self):
        """Тест 3: Создание вложенного комментария (ответ на комментарий)"""
        channel = Channel.objects.create(
            name='TestChannel',
            description='TestChannel',
            owner_id=1
        )
        
        post = Post.objects.create(
            title='My Post',
            content='Content here',
            slug='my-post',
            channel=channel,
            author_id=1
        )
        
        parent_comment = Comment.objects.create(
            post=post,
            author_id=33,
            content='Parent comment'
        )
        
        reply = Comment.objects.create(
            post=post,
            author_id=44,
            content='Child comment',
            parent=parent_comment
        )
        
        assert reply.id is not None
        assert reply.parent == parent_comment
        assert reply.parent.id == parent_comment.id
        
    def test_multiple_replies(self):
        """Тест 4: Множественные ответы на один комментарий"""
        
        channel = Channel.objects.create(
            name='TestChannel',
            description='TestChannel',
            owner_id=1
        )
        
        post = Post.objects.create(
            title='My Post',
            content='Content here',
            slug='my-post',
            channel=channel,
            author_id=1
        )
        
        parent_comment = Comment.objects.create(
            post=post,
            author_id=33,
            content='Parent comment'
        )
        
        reply1 = Comment.objects.create(
            post=post,
            author_id=44,
            content='Child comment',
            parent=parent_comment
        )
        
        
        reply2 = Comment.objects.create(
            post=post,
            author_id=44,
            content='Child comment',
            parent=parent_comment
        )
        
        assert parent_comment.replies.count() == 2
        
        replies = parent_comment.replies.all()
        assert all(reply.parent == parent_comment for reply in replies)
        assert all(reply.post == post for reply in replies)
        
        
    def test_cascade_delete_when_post_deleted(self):
        """Тест 5: Каскадное удаление комментариев при удалении поста"""
        
        channel = Channel.objects.create(
            name='TestChannel',
            description='TestChannel',
            owner_id=1
        )
        
        post = Post.objects.create(
            title='My Post',
            content='Content here',
            slug='my-post',
            channel=channel,
            author_id=1
        )
        
        parent_comment = Comment.objects.create(
            post=post,
            author_id=33,
            content='Parent comment'
        )
        
        reply1 = Comment.objects.create(
            post=post,
            author_id=44,
            content='Child comment',
            parent=parent_comment
        )
        
        
        reply2 = Comment.objects.create(
            post=post,
            author_id=44,
            content='Child comment',
            parent=parent_comment
        )
        
        reply_count = Comment.objects.filter(post=post).count()
        assert reply_count == 3
        
        reply_ids = [reply1.id, reply2.id]
        
        post.delete()
        
        assert not Post.objects.filter(id=post.id).exists()
        assert Comment.objects.count() == 0
        
        for reply_id in reply_ids:
            assert not Comment.objects.filter(id=reply_id).exists()
        
    def test_cascade_delete_replies_when_parent_deleted(self):
        """Тест 6: Каскадное удаление ответов при удалении родительского комментария"""
        channel = Channel.objects.create(
            name='Test Channel',
            description='Test',
            owner_id=1
        )
        
        post = Post.objects.create(
            channel=channel,
            title='Test Post',
            content='Content',
            author_id=1
        )
        
        parent = Comment.objects.create(
            post=post,
            author_id=1,
            content='Parent comment'
        )
        
        reply1 = Comment.objects.create(
            post=post,
            author_id=2,
            content='Reply 1',
            parent=parent
        )
        
        reply2 = Comment.objects.create(
            post=post,
            author_id=3,
            content='Reply 2',
            parent=parent
        )
        
        assert parent.replies.count() == 2
        reply1_id = reply1.id
        reply2_id = reply2.id
        
        parent.delete()
        
        assert not Comment.objects.filter(id=reply1_id).exists()
        assert not Comment.objects.filter(id=reply2_id).exists()
    
    def test_ordering(self):
        """Тест 7: Проверка ordering (по created_at DESC)"""
        channel = Channel.objects.create(
            name='Test Channel',
            description='Test',
            owner_id=1
        )
        
        post = Post.objects.create(
            channel=channel,
            title='Test Post',
            content='Content',
            author_id=1
        )
        
        comment1 = Comment.objects.create(
            post=post,
            author_id=1,
            content='First comment'
        )
        
        time.sleep(0.01)
        comment2 = Comment.objects.create(
            post=post,
            author_id=1,
            content='Second comment'
        )
        
        time.sleep(0.01)
        comment3 = Comment.objects.create(
            post=post,
            author_id=1,
            content='Third comment'
        )
        
        comments = list(Comment.objects.all())
        assert comments[0] == comment3
        assert comments[1] == comment2
        assert comments[2] == comment1
    
    def test_str_representation(self):
        """Тест 8: Строковое представление __str__"""
        channel = Channel.objects.create(
            name='Test Channel',
            description='Test',
            owner_id=1
        )
        
        post = Post.objects.create(
            channel=channel,
            title='Test Post',
            content='Content',
            author_id=1
        )
        
        comment = Comment.objects.create(
            post=post,
            author_id=123,
            content='Test comment'
        )
        
        expected = f'Comment by 123 on {post}'
        assert str(comment) == expected
        
        comment_str = str(comment)
        assert 'Comment by' in comment_str
        assert '123' in comment_str
    
    def test_author_id_field(self):
        """Тест 9: Проверка поля author_id"""
        channel = Channel.objects.create(
            name='Test Channel',
            description='Test',
            owner_id=1
        )
        
        post = Post.objects.create(
            channel=channel,
            title='Test Post',
            content='Content',
            author_id=1
        )
        
        comment1 = Comment.objects.create(
            post=post,
            author_id=100,
            content='Comment 1'
        )
        
        comment2 = Comment.objects.create(
            post=post,
            author_id=200,
            content='Comment 2'
        )
        
        comment3 = Comment.objects.create(
            post=post,
            author_id=100,
            content='Comment 3'
        )
        
        user_comments = Comment.objects.filter(author_id=100)
        assert user_comments.count() == 2
        assert comment1 in user_comments
        assert comment3 in user_comments
        assert comment2 not in user_comments
    
    def test_comment_without_parent(self):
        """Тест 10: Комментарий с пустым parent (обычный комментарий)"""
        channel = Channel.objects.create(
            name='Test Channel',
            description='Test',
            owner_id=1
        )
        
        post = Post.objects.create(
            channel=channel,
            title='Test Post',
            content='Content',
            author_id=1
        )
        
        comment = Comment.objects.create(
            post=post,
            author_id=1,
            content='Regular comment',
            parent=None
        )
        
        assert comment.parent is None
        assert comment.replies.count() == 0

pytest.mark.unit
@pytest.mark.models
class TestCommentNesting:
    def test_deep_nesting(self):
        """Тест 11 (БОНУС): Глубокая вложенность (3+ уровня)"""
        channel = Channel.objects.create(
            name='Test Channel',
            description='Test',
            owner_id=1
        )
        
        post = Post.objects.create(
            channel=channel,
            title='Test Post',
            content='Content',
            author_id=1
        )
        
        comment1 = Comment.objects.create(
            post=post,
            author_id=1,
            content='Level 1 comment'
        )
        
        reply1 = Comment.objects.create(
            post=post,
            author_id=2,
            content='Level 2 reply',
            parent=comment1
        )
        
        reply2 = Comment.objects.create(
            post=post,
            author_id=3,
            content='Level 3 reply to reply',
            parent=reply1
        )
        
        assert reply2.parent == reply1
        assert reply1.parent == comment1
        assert comment1.parent is None
        
        assert comment1.replies.count() == 1
        assert reply1.replies.count() == 1
        assert reply2.replies.count() == 0
    
    def test_root_comments_only(self):
        """Тест 12 Фильтрация только корневых комментариев"""
        channel = Channel.objects.create(
            name='Test Channel',
            description='Test',
            owner_id=1
        )
        
        post = Post.objects.create(
            channel=channel,
            title='Test Post',
            content='Content',
            author_id=1
        )
        
        comment1 = Comment.objects.create(
            post=post,
            author_id=1,
            content='Root comment 1'
        )
        
        comment2 = Comment.objects.create(
            post=post,
            author_id=1,
            content='Root comment 2'
        )
        
        reply = Comment.objects.create(
            post=post,
            author_id=2,
            content='Reply to comment1',
            parent=comment1
        )
        
        root_comments = Comment.objects.filter(parent__isnull=True)
        
        assert root_comments.count() == 2
        assert comment1 in root_comments
        assert comment2 in root_comments
        assert reply not in root_comments
    
    def test_comment_count(self):
        """Тест 13 (БОНУС): Количество комментариев к посту"""
        channel = Channel.objects.create(
            name='Test Channel',
            description='Test',
            owner_id=1
        )
        
        post = Post.objects.create(
            channel=channel,
            title='Test Post',
            content='Content',
            author_id=1
        )
        
        assert post.comments.count() == 0
        
        comment1 = Comment.objects.create(
            post=post,
            author_id=1,
            content='Comment 1'
        )
        
        comment2 = Comment.objects.create(
            post=post,
            author_id=2,
            content='Comment 2'
        )
        
        assert post.comments.count() == 2
        
        reply1 = Comment.objects.create(
            post=post,
            author_id=3,
            content='Reply 1',
            parent=comment1
        )
        
        reply2 = Comment.objects.create(
            post=post,
            author_id=4,
            content='Reply 2',
            parent=comment1
        )
        
        assert post.comments.count() == 4
        comment2.delete()
        assert post.comments.count() == 3
