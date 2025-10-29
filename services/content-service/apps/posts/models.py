from django.db import models
from django.utils.text import slugify


class Post(models.Model):
    channel = models.ForeignKey('content.Channel', on_delete=models.CASCADE, related_name='posts')
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
        super().save(*args, **kwargs)
            
    def can_edit(self, user_id, membership_role):
        return self.author_id == user_id or membership_role in ['owner', 'admin']
    
    def __str__(self) -> str:
        return f'{self.title} ({self.channel.slug})'
