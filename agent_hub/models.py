from django.db import models
from django.conf import settings
from django.utils import timezone

class AgentAction(models.Model):
    ACTION_TYPES = [
        ('submit_application', 'Submit Application to Portal'),
        ('request_referee', 'Send Referee Recommendation Request'),
        ('confirm_declaration', 'Confirm Official Legal / Ethical Declaration'),
        ('delete_document', 'Permanent Deletion of Official Document'),
        ('update_critical_profile', 'Update Official Academic Record'),
    ]

    APPROVAL_STATUSES = [
        ('pending', 'Pending Human Approval'),
        ('approved', 'Approved by User'),
        ('rejected', 'Rejected by User'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='agent_actions')
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    title = models.CharField(max_length=255)
    description = models.TextField(help_text="Detailed explanation of what the AI intends to do and why your approval is required.")
    payload = models.JSONField(default=dict, blank=True, help_text="Structured action parameters")
    status = models.CharField(max_length=30, choices=APPROVAL_STATUSES, default='pending')
    human_feedback = models.TextField(blank=True, help_text="Applicant notes or reason for rejection")
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_status_display()}] {self.title} ({self.user.email})"

    def approve(self, feedback=""):
        self.status = 'approved'
        self.human_feedback = feedback
        self.resolved_at = timezone.now()
        self.save()

    def reject(self, feedback=""):
        self.status = 'rejected'
        self.human_feedback = feedback
        self.resolved_at = timezone.now()
        self.save()


class AIAuditLog(models.Model):
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('pending_approval', 'Awaiting Approval'),
        ('warning', 'Completed with Warning'),
        ('error', 'Error / Fallback Engaged'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_audit_logs')
    action_type = models.CharField(max_length=100)
    provider = models.CharField(max_length=100, default='gemini-2.5-flash')
    summary = models.TextField()
    input_ref = models.CharField(max_length=255, blank=True)
    output_summary = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='success')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.created_at.strftime('%Y-%m-%d %H:%M')} | {self.action_type} ({self.status})"
