from django.db import models
from pytils.translit import slugify as pytils_slugify


class PortfolioItem(models.Model):
    seller_id = models.IntegerField(db_index=True)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.CharField(max_length=2000)
    main_image = models.URLField(max_length=500, blank=True, null=True)
    project_url = models.URLField(max_length=500, blank=True, null=True)
    technologies = models.JSONField(default=list, blank=True)
    completion_date = models.DateField(blank=True, null=True)
    client_name = models.CharField(max_length=100, blank=True)
    category = models.ForeignKey(
        'categories.Category',
        on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='portfolio_items'
    )
    views_count = models.PositiveIntegerField(default=0)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Работа в портфолио'
        verbose_name_plural = 'Работы в портфолио'
        ordering = ['seller_id', 'order', '-created_at']
        indexes = [
            models.Index(fields=['seller_id', '-created_at']),
        ]
        
    def save(self, *args, **kwargs):
        if not self.slug:
            
            name_with_dashes = self.title.replace('_', '-')
            base_slug = pytils_slugify(name_with_dashes)
            slug = base_slug
            counter = 1
            while PortfolioItem.objects.filter(slug=slug).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f'{self.title} by {self.seller_id}'
    
    
class PortfolioImage(models.Model):
    portfolio_item = models.ForeignKey(PortfolioItem, on_delete=models.CASCADE, related_name='images')
    image_url = models.URLField(max_length=500)
    order = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)
    caption = models.CharField(max_length=200, blank=True)
    
    class Meta:
        verbose_name = 'Изображение портфолио'
        verbose_name_plural = 'Изображения портфолио'
        ordering = ['order']
        
    def __str__(self):
        return f'Image for: {self.portfolio_item.title}'
