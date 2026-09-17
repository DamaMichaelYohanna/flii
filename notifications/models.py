from django.db import models
from django.conf import settings

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('deadline_approaching', 'Deadline Approaching'),
        ('new_opportunity', 'New Opportunity Match'),
        ('missing_document', 'Missing Application Document'),
        ('action_approval_needed', 'AI Action Requires Approval'),
        ('application_status_change', 'Application Status Updated'),
        ('system', 'System Notice'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, default='system')
    title = models.CharField(max_length=255)
    message = models.TextField()
    action_url = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} -> {self.user.email}"
