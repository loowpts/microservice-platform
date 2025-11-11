from django.db import models
from django.utils.text import slugify
from pytils.translit import slugify as pytils_slugify

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    icon = models.CharField(max_length=30, blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='subcategories' 
        )
    
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['order', 'name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = pytils_slugify(self.name)
            slug = base_slug
            slug = base_slug.replace('_', '-')
            counter = 1
            while Category.objects.filter(slug=slug).exists():
                slug=f'{base_slug}-{counter}'.replace('_', '-')
                counter += 1
            self.slug=slug
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    
