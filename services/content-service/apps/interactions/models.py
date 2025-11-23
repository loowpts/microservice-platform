from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from apps.posts.models import Post

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

class CommentLike(models.Model):
    comment = models.ForeignKey(
        'comments.Comment',
        on_delete=models.CASCADE,
        related_name='likes'
    )
    user_id = models.IntegerField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['comment', 'user_id']
