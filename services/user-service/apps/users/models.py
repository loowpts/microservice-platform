from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.utils import timezone
from django.core.validators import EmailValidator
from django.conf import settings


class UserManager(BaseUserManager):
    use_in_migrations = True
    
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('E-mail must be set')
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_user(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', False)
        extra_fields.setdefault('is_freelancer', False)
        extra_fields.setdefault('is_seller', False)
        extra_fields.setdefault('is_moderator', False)
        return self._create_user(email, password, **extra_fields)
    
    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff',True)
        extra_fields.setdefault('is_superuser',True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('is_freelancer', False)
        extra_fields.setdefault('is_seller', False)
        extra_fields.setdefault('is_moderator', False)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self._create_user(email, password, **extra_fields)
    
        
class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        'email',
        unique=True,
        db_index=True,
        validators=[EmailValidator()],
    )
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_freelancer = models.BooleanField(default=False)
    is_seller = models.BooleanField(default=False)
    is_moderator = models.BooleanField(default=False)
    
    date_joined = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        
    def __str__(self) -> str:
        return self.email

    def full_name(self):
        return (f'{self.first_name} {self.last_name}').strip()
    

class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(max_length=1000, blank=True)
    is_public = models.BooleanField(default=True)
    timezone = models.CharField(max_length=50, blank=True)
    streak_visibility = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'
        
    def __str__(self) -> str:
        return f'Профиль {self.user}'

    def role_display(self):
        roles = []
        
        if self.user.is_superuser:
            roles.append('Admin')
        elif self.user.is_moderator:
            roles.append('Moderator')
        elif self.user.is_freelancer:
            roles.append('Freelancer')
        elif self.user.is_seller:
            roles.append('Seller')
            
        return ", ".join(roles) or "User"
