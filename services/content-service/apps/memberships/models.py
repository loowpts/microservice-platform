from django.db import models
from apps.content.models import ChannelRole


class ChannelMembership(models.Model):
    channel = models.ForeignKey('content.Channel', on_delete=models.CASCADE, related_name='memberships')
    user_id = models.IntegerField(db_index=True)
    role = models.CharField(max_length=20, choices=ChannelRole.choices, default=ChannelRole.MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('channel', 'user_id')
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user_id} - {self.role} in {self.channel.name}"
