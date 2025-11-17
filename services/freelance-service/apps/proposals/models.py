from django.db import models
from django.utils import timezone


class PROPOSAL_STATUS_CHOICES(models.TextChoices):
    PENDING = 'pending', 'В ожидании'
    ACCEPTED = 'accepted', 'Принято'
    REJECTED = 'rejected', 'Отклонено'
    EXPIRED = 'expired', 'Истекло'


class CustomProposal(models.Model):
    gig = models.ForeignKey(
        'gigs.Gig',
        on_delete=models.CASCADE,
        related_name='proposals'
    )
    seller_id = models.IntegerField(db_index=True)
    buyer_id = models.IntegerField(db_index=True)
    
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=2000)
    
    price = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_days = models.PositiveIntegerField()
    revisions = models.PositiveIntegerField(default=1)
    
    status = models.CharField(
        max_length=20,
        choices=PROPOSAL_STATUS_CHOICES,
        default=PROPOSAL_STATUS_CHOICES.PENDING
        )
    
    buyer_message = models.TextField(blank=True)
    
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    accepted_at = models.DateTimeField(blank=True, null=True)
    rejected_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Кастомное предложение'
        verbose_name_plural = 'Кастомные предложения'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['seller_id', 'created_at']),
            models.Index(fields=['buyer_id', 'created_at'])
        ]
    
    def is_expired(self):
        return timezone.now() > self.expires_at

    def can_accept(self):
        return (
            self.status == PROPOSAL_STATUS_CHOICES.PENDING
            and not self.is_expired()
        )

    def mark_as_expired(self):
        if self.is_expired() and self.status == PROPOSAL_STATUS_CHOICES.PENDING:
            self.status = PROPOSAL_STATUS_CHOICES.EXPIRED
            self.save(update_fields=['status'])

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)

        super().save(*args, **kwargs)
    
    def __str__(self):
        return f'Proposal #{self.id} from {self.seller_id} to {self.buyer_id}'
    