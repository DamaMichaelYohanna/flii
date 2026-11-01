import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class AssistancePackage(models.Model):
    """
    Pay-per-application service catalogue item.
    Configurable via Django Admin. Supports both human-led and AI-assisted workflows.
    """
    CATEGORY_CHOICES = [
        ('eligibility_assessment', 'Scholarship Eligibility and Requirements Assessment'),
        ('cv_review', 'CV Review and Improvement'),
        ('motivation_letter', 'Motivation Letter Review'),
        ('personal_statement', 'Personal Statement Review'),
        ('research_proposal', 'Research Proposal Review'),
        ('full_application_review', 'Full Application Document Review'),
        ('prep_support', 'Application Preparation Support'),
        ('advisory_call', '1-on-1 Scholarship Strategy & Advisory Call'),
        ('mock_interview', 'Scholarship Mock Interview Preparation'),
        ('custom', 'Custom Mentorship & Dedicated Support'),
    ]

    DELIVERY_TYPE_CHOICES = [
        ('human_review', 'Human Professional Review'),
        ('ai_assisted', 'AI-Assisted Assessment'),
        ('hybrid', 'Hybrid (AI Initial Draft + Human Professional Polish)'),
        ('live_consultation', 'Live 1-on-1 Strategy Session'),
    ]

    SERVICE_TYPE_CHOICES = [
        ('essay_review', 'SOP & Motivation Letter Expert Review'),
        ('advisory_call', '1-on-1 Scholarship Strategy & Advisory Call'),
        ('mock_interview', 'Scholarship Mock Interview Preparation'),
        ('full_audit', 'Comprehensive Full Application Audit'),
        ('custom', 'Custom Mentorship & Dedicated Support'),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    category = models.CharField(max_length=60, choices=CATEGORY_CHOICES, default='motivation_letter')
    service_type = models.CharField(max_length=50, choices=SERVICE_TYPE_CHOICES, default='essay_review')
    delivery_type = models.CharField(max_length=40, choices=DELIVERY_TYPE_CHOICES, default='human_review')
    requires_human_review = models.BooleanField(default=True, help_text="True if a qualified human reviewer is required.")
    tagline = models.CharField(max_length=255, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=5000.00, help_text="Configurable price in NGN")
    price_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Optional upper price limit for range display (e.g. ₦5,000–₦8,000)")
    currency = models.CharField(max_length=10, default='NGN')
    estimated_delivery_time = models.CharField(max_length=100, default="3 business days", help_text="e.g. 48 hours, 3 business days")
    turnaround_days = models.PositiveIntegerField(default=3, help_text="Estimated turnaround in calendar days")
    service_instructions = models.TextField(blank=True, help_text="Clear instructions for the applicant prior to purchase.")
    document_requirements = models.TextField(blank=True, help_text="Optional document requirements (e.g. Draft CV, Transcript, Essay draft).")
    features = models.JSONField(default=list, help_text="List of bullet points included in package")
    badge = models.CharField(max_length=50, blank=True, help_text="e.g. Most Popular, High Impact, Admissions Grade")
    icon = models.CharField(max_length=50, default='file-check', help_text="Lucide icon name")
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'price']
        verbose_name = 'Service Catalogue Item'
        verbose_name_plural = 'Service Catalogue Items'

    def __str__(self):
        if self.price_max and self.price_max > self.price:
            return f"{self.name} (₦{self.price:,.0f}–₦{self.price_max:,.0f} {self.currency})"
        return f"{self.name} (₦{self.price:,.0f} {self.currency})"

    @property
    def formatted_price(self):
        if self.price_max and self.price_max > self.price:
            return f"₦{self.price:,.0f}–₦{self.price_max:,.0f}"
        return f"₦{self.price:,.0f}"


# Model Alias for conceptual symmetry
ServiceCatalogItem = AssistancePackage


class AssistanceBooking(models.Model):
    """
    Pay-per-application service order submitted by an applicant.
    Adheres strictly to required workflow statuses and reviewer data isolation.
    """
    STATUS_CHOICES = [
        ('pending_payment', 'Pending Payment'),
        ('paid', 'Paid'),
        ('awaiting_assignment', 'Awaiting Assignment'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('awaiting_user_info', 'Awaiting User Information'),
        ('ready_for_review', 'Ready for Review'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
        # Legacy status compatibility
        ('confirmed', 'Confirmed & Queued'),
        ('in_review', 'Under Expert Review'),
        ('scheduled', 'Session Scheduled'),
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

    order_number = models.CharField(max_length=50, unique=True, blank=True, db_index=True)
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
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='NGN')
    urgency = models.CharField(max_length=30, choices=URGENCY_CHOICES, default='standard')

    # Scheduling preferences
    preferred_date = models.DateField(null=True, blank=True)
    preferred_time_slot = models.CharField(max_length=50, choices=TIME_SLOT_CHOICES, default='afternoon')

    # Requirements & Documents
    applicant_notes = models.TextField(
        help_text="Please describe your background, current status, and specific questions or goals for the reviewer."
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
        default='email'
    )

    # Workflow & Payment
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default='pending_payment')
    payment_status = models.CharField(max_length=40, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    payment_reference = models.CharField(
        max_length=150,
        blank=True,
        help_text="Payment transaction reference"
    )
    payment_transaction = models.ForeignKey(
        'subscriptions.PaymentTransaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='service_orders'
    )
    payment_proof = models.FileField(
        upload_to='assistance/payments/%Y/%m/',
        blank=True,
        null=True,
        help_text="Receipt or proof of payment screenshot"
    )

    # Reviewer Management & Fulfillment
    assigned_reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_service_orders'
    )
    # Legacy alias
    assigned_admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_assistance_bookings'
    )
    admin_notes = models.TextField(blank=True, help_text="Internal confidential notes for administrators and reviewers")
    meeting_link = models.URLField(blank=True, help_text="Live Google Meet or Zoom URL assigned by reviewer")
    scheduled_at = models.DateTimeField(null=True, blank=True, help_text="Confirmed call date & time")
    
    # Information requests from reviewer
    additional_docs_requested = models.BooleanField(default=False)
    additional_docs_notes = models.TextField(blank=True, help_text="Specific additional details or files requested from applicant")

    # Deliverables
    deliverable_feedback = models.TextField(blank=True, help_text="Review feedback, annotations, and strategic notes for applicant")
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
        verbose_name = 'Service Order'
        verbose_name_plural = 'Service Orders'

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        if self.assigned_reviewer and not self.assigned_admin:
            self.assigned_admin = self.assigned_reviewer
        elif self.assigned_admin and not self.assigned_reviewer:
            self.assigned_reviewer = self.assigned_admin
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.get_status_display()}] #{self.order_number} {self.package_title} - {self.user.email}"

    @property
    def is_call_service(self):
        return self.service_type in ['advisory_call', 'mock_interview', 'full_audit']

    @property
    def effective_scholarship_title(self):
        if self.application and self.application.opportunity:
            return self.application.opportunity.title
        return self.target_scholarship or "General Postgraduate Application"

    @property
    def formatted_price(self):
        return f"₦{self.price:,.0f}"


# Model Alias for conceptual symmetry
ServiceOrder = AssistanceBooking
