from django.db import models
from pytils.translit import slugify as pytils_slugify
from django.db.models import Avg, Count, F

from apps.reviews.models import Review
from apps.orders.models import Order

class GIG_STATUS_CHOICES(models.TextChoices):
    DRAFT = 'draft', 'Черновик'
    PENDING_APPROVAL = 'pending_approval', 'На модерации'
    ACTIVE = 'active', 'Активен'
    PAUSED = 'paused', 'Приостановлен'
    ARCHIVED = 'archived', 'В архиве'


class PACKAGE_TYPE_CHOICES(models.TextChoices):
    BASIC = 'basic', 'Базовый'
    STANDARD = 'standard', 'Стандартный'
    PREMIUM = 'premium', 'Премиум'
    
class Gig(models.Model):
    seller_id = models.IntegerField(db_index=True)
    category = models.ForeignKey(
        'categories.Category',
        on_delete=models.PROTECT,
        related_name='gigs'
        )
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(max_length=5000)
    
    main_image = models.URLField(max_length=500, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=GIG_STATUS_CHOICES,
        default=GIG_STATUS_CHOICES.DRAFT
        )
    
    views_count = models.PositiveIntegerField(default=0)
    orders_count = models.PositiveIntegerField(default=0)
    
    rating_average = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    reviews_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['seller_id', 'status']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['rating_average']),
            models.Index(fields=['-created_at']),
        ]
        
    def save(self, *args, **kwargs):
        if not self.slug:
            
            name_with_dashes = self.title.replace('_', '-')
            base_slug = pytils_slugify(name_with_dashes)
            slug = base_slug
            counter = 1
            while Gig.objects.filter(slug=slug).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    def update_rating(self):
        stats = (
            Review.objects.filter(gig=self, is_active=True)
            .aggregate(
                avg_rating=Avg('rating'),
                total_reviews=Count('id')
            )
        )
        
        self.rating_average = stats['avg_rating'] or 0
        self.reviews_count = stats['total_reviews'] or 0
        self.save(update_fields=['rating_average', 'reviews_count', 'updated_at'])
        
        return self.rating_average
    
    def update_orders_count(self):
        completed_orders = Order.objects.filter(
            gig=self,
            status='completed'
        ).count()
        
        self.orders_count = completed_orders
        self.save(update_fields=['orders_count', 'updated_at'])
        return self.orders_count
    
    def increment_views(self):
        self.__class__.objects.filter(pk=self.pk).update(views_count=F('views_count') + 1)
        self.refresh_from_db(fields=['views_count'])
        return self.views_count
    
    def __str__(self):
        return self.title
    
class GigPackage(models.Model):
    gig = models.ForeignKey(
        Gig,
        on_delete=models.CASCADE,
        related_name='packages'
    )
    package_type = models.CharField(max_length=20, choices=PACKAGE_TYPE_CHOICES)
    
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=1000)
    
    price = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_time = models.PositiveIntegerField() # В днях
    
    revisions = models.PositiveIntegerField(default=1)
    features = models.JSONField(default=list, blank=True) # ["Feature 1", "Feature 2"]
    
    class Meta:
        verbose_name = 'Пакет услуги'
        verbose_name_plural = 'Пакеты услуг'
        unique_together = ['gig', 'package_type']
        ordering = ['package_type']
    
    def __str__(self):
        return f"{self.gig.title} — {self.get_package_type_display()}"
class GigImage(models.Model):
    gig = models.ForeignKey(Gig, on_delete=models.CASCADE, related_name='images')
    image_url = models.URLField(max_length=500)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    caption = models.CharField(max_length=200, blank=True)
    
    class Meta:
        verbose_name = 'Изображение услуги'
        verbose_name_plural = 'Изображения услуг'
        ordering = ['order']
        
    def __str__(self):
        return f'Image for {self.gig.title}'
    
class GigTag(models.Model):
    gig = models.ForeignKey(Gig, on_delete=models.CASCADE, related_name='tags')
    tag = models.CharField(max_length=50)
    
    class Meta:
        verbose_name = 'Тег услуги'
        verbose_name_plural = 'Теги услуг'
        unique_together = ['gig', 'tag']
        
    def __str__(self):
        return f'{self.gig.title} - {self.tag}'
    
