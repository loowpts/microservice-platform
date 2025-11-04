from django.db import models
from django.utils.text import slugify

class CONDITION_CHOICES(models.TextChoices):
    NEW = 'new', 'Новый'
    USED = 'used', 'Б/У'
    REFURBISHED = 'refurbished', 'Восстановленный'

class STATUS_CHOICES(models.TextChoices):
    ACTIVE = 'active', 'Активен'
    SOLD = 'sold', 'Продан'
    archived = 'archived', 'В архиве'
    DRAFT = 'draft', 'Черновик'

class Product(models.Model):
    category = models.ForeignKey('categories.Category', on_delete=models.CASCADE, related_name='products')
    title = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=150, unique=True)
    description = models.TextField(max_length=1000)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    main_image = models.URLField(max_length=500, blank=True, null=True)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    seller_id = models.IntegerField(db_index=True)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default=CONDITION_CHOICES.NEW)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_CHOICES.DRAFT)
    city = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(default=1)
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['-created_at']
        
        indexes = [
            models.Index(fields=['seller_id', 'status']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['created_at'])
        ]
        
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                slug=f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
        
    def __str__(self):
        return self.title
    

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='additional_images')
    image_url = models.URLField(max_length=500)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f'Image for {self.product.title}'
    
    
        
    
    
