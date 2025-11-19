from django.db import models


class Favorite(models.Model):
    user_id = models.IntegerField(db_index=True)
    gig = models.ForeignKey(
        'gigs.Gig',
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        ordering = ['-created_at']
        unique_together = ['user_id', 'gig']
        indexes = [
            models.Index(fields=['user_id', '-created_at'])
        ]
        
    def __str__(self):
        return f'User {self.user_id} -> Gig {self.gig.title}'
    
