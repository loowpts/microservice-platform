from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, UserProfile
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        logger.info(f'Profile created for user: {instance.email}')

@receiver(post_save, sender=User)
def log_roles(sender, instance, **kwargs):
    logger.info(f"User {instance.email} roles: freelancer={instance.is_freelancer}, seller={instance.is_seller}, moderator={instance.is_moderator}")
