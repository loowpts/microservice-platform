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
        
#     def test_multiple_replies(self):
#         """Тест 4: Множественные ответы на один комментарий"""
#         pass
    
#     def test_cascade_delete_when_post_deleted(self):
#         """Тест 5: Каскадное удаление комментариев при удалении поста"""
#         pass
    
#     def test_cascade_delete_replies_when_parent_deleted(self):
#         """Тест 6: Каскадное удаление ответов при удалении родительского комментария"""
#         pass
    
#     def test_ordering(self):
#         """Тест 7: Проверка ordering (по created_at DESC)"""
#         pass
    
#     def test_str_representation(self):
#         """Тест 8: Строковое представление __str__"""
#         pass
    
#     def test_author_id_field(self):
#         """Тест 9: Проверка поля author_id"""
#         pass
    
#     def test_comment_without_parent(self):
#         """Тест 10: Комментарий с пустым parent (обычный комментарий)"""
#         pass


# @pytest.mark.unit
# @pytest.mark.models
# class TestCommentNesting:
#     def test_deep_nesting(self):
#         """Тест 11 (БОНУС): Глубокая вложенность (3+ уровня)"""
#         pass
    
#     def test_root_comments_only(self):
#         """Тест 12 (БОНУС): Фильтрация только корневых комментариев"""
#         pass
    
#     def test_comment_count(self):
#         """Тест 13 (БОНУС): Количество комментариев к посту"""
#         pass
