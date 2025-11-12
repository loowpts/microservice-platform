from django.db import models
from django.utils.text import slugify
from pytils.translit import slugify as pytils_slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(max_length=500, blank=True)
    icon_url = models.URLField(max_length=500, blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Категория'    
        verbose_name_plural = 'Категории'
        ordering = ['order', 'name']    

    def save(self, *args, **kwargs):

        if not self.slug:            
            name_with_dashes = self.name.replace('_', '-')
            base_slug = pytils_slugify(name_with_dashes)
            slug = base_slug
            counter = 1
            
            while Category.objects.filter(slug=slug).exists():
                slug = f'{slug}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
        
    def __str__(self):
        return self.name
    
class Subcategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(max_length=500, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Подкатегория'
        verbose_name_plural = 'Подкатегории'
        ordering = ['order', 'name']
        unique_together = ['category', 'name']
        
    def save(self, *args, **kwargs):

        if not self.slug:            
            name_with_dashes = self.name.replace('_', '-')
            base_slug = pytils_slugify(name_with_dashes)
            slug = base_slug
            counter = 1
            
            while Category.objects.filter(slug=slug).exists():
                slug = f'{slug}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f'{self.category.name} - {self.name}'
    
