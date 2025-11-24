from django.db import models
from django.utils.text import slugify
from django.db.models import F


class Post(models.Model):
    channel = models.ForeignKey('content.Channel', on_delete=models.CASCADE, related_name='posts')
    author_id = models.IntegerField(db_index=True)
    title = models.CharField(max_length=200, unique=True)
    slug = models.CharField(max_length=200, unique=True)
    content = models.TextField()
    image_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ('channel', 'slug')
        ordering = ['-created_at']
        
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Post.objects.filter(channel=self.channel, slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
            
    def can_edit(self, user_id, membership_role):
        return self.author_id == user_id or membership_role in ['owner', 'admin']
    
    def __str__(self) -> str:
        return f'{self.title} ({self.channel.slug})'
    
    def increment_views(self):
        Post.objects.filter(pk=self.pk).update(view_count=F('view_count') + 1)
    
    def update_like_count(self):
        """Обновить счетчик лайков"""
        self.like_count = self.likes.count()
        self.save(update_fields=['like_count'])
        
    def update_comment_count(self):
        """Обновить счетчик комментариев"""
        self.comment_count = self.comments.count()
        self.save(update_fields=['comment_count'])
    
        
    
    
