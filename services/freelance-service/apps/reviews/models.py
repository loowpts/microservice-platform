from django.db import models
from django.core.exceptions import ValidationError

class Review(models.Model):
    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='review'
    )
    gig = models.ForeignKey(
        'gigs.Gig',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    buyer_id = models.IntegerField(db_index=True)
    seller_id = models.IntegerField(db_index=True)
    rating = models.PositiveSmallIntegerField(
            choices=[(i, str(i)) for i in range(1, 6)],
            default=1
        )
    comment = models.TextField(max_length=2000)
    communication_rating = models.PositiveSmallIntegerField(blank=True, null=True)
    service_quality_rating = models.PositiveSmallIntegerField(blank=True, null=True)
    delivery_rating = models.PositiveSmallIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['gig', '-created_at']),
            models.Index(fields=['seller_id', '-created_at']),
        ]
    
    def __str__(self):
        return f'Review for Order #{self.order.id}'
    
    def clean(self) -> None:
        if not (1 <= self.rating <= 5):
            raise ValidationError(
                {'rating': 'Оценка должна быть от 1 до 5.'}
                )
            
        for field in ['communication_rating', 'service_quality_rating', 'delivery_rating']:
            value = getattr(self, field)
            if value is not None and not (1 <= value <= 5):
                raise ValidationError({field: 'Оценка должна быть от 1 до 5.'})
            
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.gig.update_rating()
        
        
class ReviewReply(models.Model):
    review = models.OneToOneField(
        Review,
        on_delete=models.CASCADE,
        related_name='reply'
    )
    message = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Ответ на отзыв'
        verbose_name_plural = 'Ответы на отзывы'

    def __str__(self):
        return f'Reply to Review #{self.review.id}'
