from django.db import models
from django.utils import timezone
from datetime import timedelta

class ORDER_STATUS_CHOICES(models.TextChoices):
    PENDING = 'pending', 'Ожидает подтверждения'
    IN_PROGRESS = 'in_progress', 'В работе'
    DELIVERED = 'delivered', 'Доставлен (ожидает приемки)'
    COMPLETED = 'completed', 'Завершен'
    CANCELLED = 'cancelled', 'Отменен'
    DISPUTED = 'disputed', 'Спор'


class Order(models.Model):
    gig = models.ForeignKey(
        'gigs.Gig',
        on_delete=models.PROTECT,
        related_name='orders'
    )
    package = models.ForeignKey(
        'gigs.GigPackage',
        on_delete=models.PROTECT,
        related_name='orders'
    )
    buyer_id = models.IntegerField(db_index=True)
    seller_id = models.IntegerField(db_index=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default=ORDER_STATUS_CHOICES.PENDING)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_time = models.PositiveIntegerField()
    requirements = models.TextField(max_length=3000, blank=True)
    deadline = models.DateTimeField()
    delivered_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['buyer_id', 'status']),
            models.Index(fields=['seller_id', 'status']),
            models.Index(fields=['status']),
        ]  
    
    def __str__(self):
        return f'Order #{self.id} - {self.gig.title}'
    
    def save(self, *args, **kwargs):
        if not self.pk:
            self.deadline = timezone.now() + timedelta(days=self.delivery_time)
        super().save(*args, **kwargs)
    
    def can_be_cancelled(self):
        return self.status in ['pending', 'in_progress']
    
    def can_be_delivered(self):
        return self.status == 'in_progress' 
    
    def can_be_completed(self):
        return self.status == 'delivered'
    
    def is_overdue(self):
        return (
            timezone.now() > self.deadline and 
            self.status in ['pending', 'in_progress']
        )
    

class OrderDelivery(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='deliveries'
    )
    message = models.TextField(max_length=2000)
    file_url = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Доставка результата'
        verbose_name_plural = 'Доставки результатов'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Delivery for Order #{self.order.id}'
    

class OrderRequirement(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='requirement_files'
    )
    file_url = models.URLField(max_length=500)
    description = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Файл требования'
        verbose_name_plural = 'Файлы требований'
        
    def __str__(self):
        return f'Requirements for Order #{self.order.id}'
    
    

