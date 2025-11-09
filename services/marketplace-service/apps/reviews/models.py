from django.db import models
from django.utils.text import slugify


class Review(models.Model):
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='reviews',
        )
    author_id = models.IntegerField(db_index=True)
    rating = models.PositiveSmallIntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        default=1
    )
    comment = models.TextField()
    pros = models.TextField(blank=True)
    cons = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        unique_together = ['product', 'author_id']
        ordering = ['-created_at']
        
    def __str__(self):
        return f'Review by {self.author_id} for {self.product.title}'
    
        
