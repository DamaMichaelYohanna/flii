from django.db import models
from django.conf import settings
from django.utils import timezone


class AssistancePackage(models.Model):
    """
    Preset paid assistance offerings provided by platform administrators/mentors.
    """
    SERVICE_TYPE_CHOICES = [
        ('essay_review', 'SOP & Motivation Letter Expert Review'),
        ('advisory_call', '1-on-1 Scholarship Strategy & Advisory Call'),
        ('mock_interview', 'Scholarship Mock Interview Preparation'),
        ('full_audit', 'Comprehensive Full Application Audit'),
        ('custom', 'Custom Mentorship & Dedicated Support'),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    service_type = models.CharField(max_length=50, choices=SERVICE_TYPE_CHOICES, default='essay_review')
    tagline = models.CharField(max_length=255, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2, default=49.00)
    currency = models.CharField(max_length=10, default='USD')
    turnaround_days = models.PositiveIntegerField(default=3, help_text="Estimated turnaround in days")
    features = models.JSONField(default=list, help_text="List of bullet points included in package")
    badge = models.CharField(max_length=50, blank=True, help_text="e.g. Most Popular, High Impact")
    icon = models.CharField(max_length=50, default='file-check', help_text="Lucide icon name")
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'price']
        verbose_name = 'Assistance Package'
        verbose_name_plural = 'Assistance Packages'

    def __str__(self):
        return f"{self.name} (${self.price} {self.currency})"


class AssistanceBooking(models.Model):
    """
    Paid assistance booking submitted by an applicant to the platform administrator.
    """
    STATUS_CHOICES = [
        ('pending_payment', 'Pending Confirmation / Payment'),
        ('confirmed', 'Confirmed & Queued'),
        ('in_review', 'Under Expert Review'),
        ('scheduled', 'Session Scheduled'),
        ('completed', 'Completed & Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('pending_verification', 'Pending Verification'),
        ('paid', 'Paid & Verified'),
        ('waived', 'Waived / Free Grant'),
    ]

    URGENCY_CHOICES = [
        ('standard', 'Standard (3-5 Business Days)'),
        ('priority', 'Priority (48 Hours, +25%)'),
        ('rush', 'Rush (24 Hours, +50%)'),
    ]

    TIME_SLOT_CHOICES = [
        ('morning', 'Morning (09:00 - 12:00 UTC)'),
        ('afternoon', 'Afternoon (13:00 - 17:00 UTC)'),
        ('evening', 'Evening (18:00 - 21:00 UTC)'),
        ('flexible', 'Flexible / Anytime'),
    ]

    CONTACT_METHOD_CHOICES = [
        ('google_meet', 'Google Meet'),
        ('zoom', 'Zoom'),
        ('whatsapp', 'WhatsApp Audio / Chat'),
        ('email', 'Email Only (Async Written Review)'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assistance_bookings'
    )
    package = models.ForeignKey(
        AssistancePackage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings'
    )
    service_type = models.CharField(
        max_length=50,
        choices=AssistancePackage.SERVICE_TYPE_CHOICES,
        default='essay_review'
    )
    package_title = models.CharField(max_length=200)

    # Optional linkage to an active Application in workspace
    application = models.ForeignKey(
        'applications.Application',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assistance_bookings'
    )
    target_scholarship = models.CharField(max_length=255, blank=True, help_text="e.g. Erasmus Mundus, DAAD EPOS, Chevening")
    target_university = models.CharField(max_length=255, blank=True)

    # Pricing & Urgency
    price = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    urgency = models.CharField(max_length=30, choices=URGENCY_CHOICES, default='standard')

    # Scheduling preferences
    preferred_date = models.DateField(null=True, blank=True)
    preferred_time_slot = models.CharField(max_length=50, choices=TIME_SLOT_CHOICES, default='afternoon')

    # Requirements & Documents
    applicant_notes = models.TextField(
        help_text="Please describe your background, current status, and specific questions or goals for the admin team."
    )
    attached_document = models.FileField(
        upload_to='assistance/submissions/%Y/%m/',
        blank=True,
        null=True,
        help_text="Direct upload of your draft essay, CV, or proposal."
    )
    document_vault_ref = models.ForeignKey(
        'documents.Document',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assistance_bookings',
        help_text="Optionally select an existing document from your Document Vault."
    )

    # Contact preferences
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=50, blank=True, help_text="WhatsApp number or phone with country code")
    preferred_contact_method = models.CharField(
        max_length=30,
        choices=CONTACT_METHOD_CHOICES,
        default='google_meet'
    )

    # Workflow & Payment
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default='pending_payment')
    payment_status = models.CharField(max_length=40, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    payment_reference = models.CharField(
        max_length=150,
        blank=True,
        help_text="Transaction reference, bank transfer ID, or payment confirmation code"
    )
    payment_proof = models.FileField(
        upload_to='assistance/payments/%Y/%m/',
        blank=True,
        null=True,
        help_text="Receipt or proof of payment screenshot"
    )

    # Admin Fulfillment
    assigned_admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_assistance_bookings'
    )
    admin_notes = models.TextField(blank=True, help_text="Internal notes for administrators")
    meeting_link = models.URLField(blank=True, help_text="Live Google Meet or Zoom URL assigned by admin")
    scheduled_at = models.DateTimeField(null=True, blank=True, help_text="Confirmed call date & time")
    deliverable_feedback = models.TextField(blank=True, help_text="Review feedback and strategic notes for the applicant")
    deliverable_file = models.FileField(
        upload_to='assistance/deliverables/%Y/%m/',
        blank=True,
        null=True,
        help_text="Reviewed annotated document or comprehensive audit report"
    )
    completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Assistance Booking'
        verbose_name_plural = 'Assistance Bookings'

    def __str__(self):
        return f"[{self.get_status_display()}] {self.package_title} - {self.user.email}"

    @property
    def is_call_service(self):
        return self.service_type in ['advisory_call', 'mock_interview', 'full_audit']

    @property
    def effective_scholarship_title(self):
        if self.application and self.application.opportunity:
            return self.application.opportunity.title
        return self.target_scholarship or "General Postgraduate Application"
