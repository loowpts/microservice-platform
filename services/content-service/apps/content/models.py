from django.db import models
from django.utils.text import slugify
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from .proxies import UserProxy
from .api import get_user

class Channel(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    owner_id = models.IntegerField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = 'Канал'
        verbose_name_plural = 'Каналы'
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    @property
    def get_owner(self):
        user_data = get_user(self.owner_id)
        if user_data:
            return UserProxy.from_api(user_data)
        return None
    
    def __str__(self) -> str:
        return self.name
    
    
class ChannelRole(models.TextChoices):
    OWNER = "owner", "Owner"
    ADMIN = "admin", "Admin"
    MODERATOR = "moderator", "Moderator"
    MEMBER = "member", "Member"


class ChannelMembership(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='memberships')
    user_id = models.IntegerField(db_index=True)
    role = models.CharField(max_length=20, choices=ChannelRole.choices, default=ChannelRole.MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('channel', 'user_id')
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user_id} in {self.channel.slug} as {self.role}"
    
    def get_user(self):
        user_data = get_user(self.user_id)
        if user_data:
            return UserProxy.from_api(user_data)
        return None
    
class Post(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='posts')
    author_id = models.IntegerField(db_index=True)
    title = models.CharField(max_length=200, unique=True)
    slug = models.CharField(max_length=200, unique=True)
    content = models.TextField()
    image_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('channel', 'slug')
        ordering = ['-created_at']
        
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            
    def can_edit(self, user_id, membership_role):
        return self.author_id == user_id or membership_role in ['owner', 'admin']
    
    def __str__(self) -> str:
        return f'{self.title} ({self.channel.slug})'
    
    def get_author(self):
        user_data = get_user(self.author_id)
        if user_data:
            return UserProxy.from_api(user_data)
        return None
    
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author_id = models.IntegerField(db_index=True)
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def get_author(self):
        user_data = get_user(self.author_id)
        if user_data:
            return UserProxy.from_api(user_data)
        return None
    
    def __str__(self) -> str:
        return f'Comment by {self.author_id} on {self.post}'
    
class Like(models.Model):
    user_id = models.IntegerField(db_index=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('user_id', 'content_type', 'object_id')
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]
        
    def __str__(self) -> str:
        return f'Like by {self.user_id} on {self.content_type} ({self.object_id})'
    
    def get_user(self):
        user_data = get_user(self.user_id)
        if user_data:
            return UserProxy.from_api(user_data)
        return None

class View(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='views')
    user_id = models.IntegerField(null=True, blank=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-viewed_at']
        
    def __str__(self) -> str:
        return f'View of {self.post} by {self.user_id or self.ip_address})'

    def get_user(self):
        user_data = get_user(self.user_id)
        if user_data:
            return UserProxy.from_api(user_data)
        return None
