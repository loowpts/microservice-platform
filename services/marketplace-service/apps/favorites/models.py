from django.db import models


class Favorite(models.Model):
    user_id = models.IntegerField(db_index=True)
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='favorites'
        )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user_id', 'product']
        ordering = ['-created_at']
        
    def __str__(self):
        return f'User {self.user_id} - {self.product.title}'
    
    
