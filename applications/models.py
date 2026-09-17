from django.db import models
from django.conf import settings
from opportunities.models import Opportunity
from documents.models import Document

class Application(models.Model):
    STATUS_CHOICES = [
        ('planning', 'Planning & Evaluation'),
        ('preparing', 'Preparing Documents'),
        ('in_progress', 'In Progress (Writing Essays)'),
        ('ready_for_review', 'Ready for Final Review'),
        ('submitted', 'Submitted to Portal'),
        ('interview', 'Invited to Interview'),
        ('offer', 'Offer Received (Scholarship Awarded)'),
        ('rejected', 'Unsuccessful'),
        ('withdrawn', 'Withdrawn'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications')
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='planning')
    personal_notes = models.TextField(blank=True)
    target_submission_date = models.DateField(null=True, blank=True)
    submission_confirmation_id = models.CharField(max_length=150, blank=True, help_text="Official confirmation number upon user manual submission")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        unique_together = ('user', 'opportunity')

    def __str__(self):
        return f"{self.user.get_full_name()} -> {self.opportunity.title} ({self.get_status_display()})"

    @property
    def progress_percentage(self):
        total_reqs = self.requirements.count()
        if total_reqs == 0:
            return 10
        completed = self.requirements.filter(status='complete').count()
        in_progress = self.requirements.filter(status='in_progress').count() * 0.5
        needs_review = self.requirements.filter(status='needs_review').count() * 0.8
        pct = int(((completed + in_progress + needs_review) / total_reqs) * 100)
        return min(100, max(0, pct))

    @property
    def missing_documents_count(self):
        return self.requirements.filter(is_mandatory=True, status__in=['not_started', 'in_progress']).count()


class ApplicationRequirement(models.Model):
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress / Drafting'),
        ('needs_review', 'Draft Ready / Needs Review'),
        ('complete', 'Complete & Verified'),
        ('not_applicable', 'Not Applicable'),
    ]

    REQUIREMENT_TYPE_CHOICES = [
        ('document', 'Document Upload (PDF/Scan)'),
        ('essay', 'Essay / Written Response'),
    ]

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='requirements')
    name = models.CharField(max_length=255, help_text="e.g. Motivation Letter / Statement of Purpose")
    description = models.TextField(blank=True)
    requirement_type = models.CharField(max_length=20, choices=REQUIREMENT_TYPE_CHOICES, default='document')
    is_mandatory = models.BooleanField(default=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='not_started')
    due_date = models.DateField(null=True, blank=True)
    attached_document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, blank=True, related_name='requirement_attachments')
    draft_response = models.TextField(blank=True, help_text="Working response / essay content for this requirement")
    ai_grounding_notes = models.TextField(blank=True, help_text="AI alignment checks and verified fact citations")
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.application.opportunity.title}: {self.name} [{self.get_status_display()}]"

    @property
    def is_document(self):
        return self.requirement_type == 'document'

    @property
    def is_essay(self):
        return self.requirement_type == 'essay'



class ApplicationTask(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)
    due_date = models.DateField(null=True, blank=True)
    created_by_ai = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['is_completed', 'due_date', '-created_at']

    def __str__(self):
        return f"Task: {self.title} ({'Done' if self.is_completed else 'Pending'})"
