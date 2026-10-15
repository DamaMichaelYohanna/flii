from django.db import models
from django.conf import settings
from django.utils import timezone

class OpportunitySource(models.Model):
    SOURCE_TYPES = [
        ('erasmus', 'Erasmus+ / European Commission'),
        ('government', 'Government Scholarship Body (e.g. DAAD, Chevening, FCDO)'),
        ('university', 'University Direct Award'),
        ('foundation', 'Philanthropic Foundation (e.g. Mastercard Foundation)'),
        ('research_institute', 'Research Institution / National Lab'),
        ('other', 'Other Verified Provider'),
    ]

    name = models.CharField(max_length=255)
    source_url = models.URLField(max_length=500)
    source_type = models.CharField(max_length=50, choices=SOURCE_TYPES, default='government')
    is_active = models.BooleanField(default=True)
    last_status = models.CharField(max_length=50, default='idle')
    last_error = models.TextField(blank=True)
    items_found_count = models.IntegerField(default=0)
    last_checked = models.DateTimeField(default=timezone.now)
    last_verified = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"


class Opportunity(models.Model):
    DEGREE_LEVELS = [
        ('masters', "Master's Degree (MSc / MA / MEng / LLM)"),
        ('phd', 'Doctorate (PhD / DPhil)'),
        ('fellowship', 'Fellowship / Research Stay'),
        ('bachelors', "Bachelor's Degree"),
        ('postdoc', 'Postdoctoral Fellowship'),
    ]

    FUNDING_TYPES = [
        ('fully_funded', 'Fully Funded (100% Tuition + Living Allowance + Travel + Health Insurance)'),
        ('partial', 'Partial Funding / Fee Reduction + Partial Stipend'),
        ('tuition_waiver', '100% Tuition Fee Waiver Only'),
        ('stipend_only', 'Monthly Living Stipend Only'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active & Open'),
        ('upcoming', 'Upcoming Call'),
        ('deadline_passed', 'Deadline Passed'),
        ('closed', 'Closed'),
        ('archived', 'Archived'),
    ]

    VERIFICATION_STATUSES = [
        ('source_verified', 'Source Verified (Human / Official Agency Confirmed)'),
        ('ai_extracted', 'AI Extracted from Official Portal'),
        ('needs_review', 'Needs Review / Policy Update'),
        ('unverified', 'Unverified'),
        ('expired', 'Expired'),
    ]

    title = models.CharField(max_length=255)
    provider = models.CharField(max_length=255, help_text="e.g. European Union, DAAD, British Council, Rhodes Trust")
    university = models.CharField(max_length=255, blank=True, help_text="Specific University or Consortium (e.g. Consortium of 3 EU Universities)")
    country = models.CharField(max_length=100, help_text="e.g. Germany, United Kingdom, France, European Union (Multi-Country)")
    degree_level = models.CharField(max_length=50, choices=DEGREE_LEVELS, default='masters')
    field_of_study = models.CharField(max_length=255, help_text="e.g. Computer Science, Artificial Intelligence, Data Science, Public Policy")
    description = models.TextField()
    
    funding_type = models.CharField(max_length=50, choices=FUNDING_TYPES, default='fully_funded')
    funding_details = models.TextField(help_text="Detailed allowance breakdown (stipend amount, flight ticket, visa allowance, health insurance)")
    eligibility_summary = models.TextField(help_text="Clear bulleted breakdown of who can apply")
    
    application_url = models.URLField(max_length=500, help_text="Direct link to application portal")
    official_source_url = models.URLField(max_length=500, help_text="Official scholarship documentation page")
    source = models.ForeignKey(OpportunitySource, on_delete=models.SET_NULL, null=True, blank=True, related_name='opportunities')
    
    opening_date = models.DateTimeField(null=True, blank=True, help_text="Official opening date of application window")
    deadline = models.DateTimeField(help_text="Official application deadline")
    deadline_timezone = models.CharField(max_length=50, default='UTC', help_text="e.g. CET, GMT, UTC, EST")
    cycle_name = models.CharField(max_length=100, default="2026/2027 Academic Year", help_text="e.g. 2026/2027 Annual Cycle")
    start_date = models.DateField(null=True, blank=True, help_text="Academic intake start")
    duration = models.CharField(max_length=100, default="24 Months (2 Years)")
    
    language_requirement = models.TextField(help_text="e.g. IELTS 6.5+, TOEFL 90+, or English medium of instruction certificate accepted")
    academic_requirement = models.TextField(help_text="e.g. Bachelor's degree with minimum Second Class Upper (2:1) or First Class honours")
    work_experience_requirement = models.TextField(blank=True, help_text="e.g. 2 years relevant experience, or none required for recent graduates")
    nationality_requirement = models.TextField(help_text="e.g. Open to all nationalities, or DAC-listed developing countries (including Nigeria)")
    documents_required = models.TextField(help_text="List of mandatory documents (CV, Statement of Purpose, Transcripts, 2 Reference Letters, Passport)")
    
    application_fee = models.CharField(max_length=100, default='Free / No Application Fee')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='active')
    verification_status = models.CharField(max_length=30, choices=VERIFICATION_STATUSES, default='source_verified')
    portal_type = models.CharField(
        max_length=50,
        default='direct_portal',
        choices=[
            ('direct_portal', 'Direct Online Application Portal'),
            ('external_portal', 'External University / Central System'),
            ('nomination_required', 'National Agency Nomination Required'),
            ('email_submission', 'Direct Email Dossier Submission')
        ]
    )
    ai_application_readiness = models.CharField(
        max_length=50,
        default='ready',
        choices=[
            ('ready', 'Verified Active Apply Portal'),
            ('requires_login', 'Requires Account Registration First'),
            ('not_yet_open', 'Application Portal Locked Until Opening Date'),
            ('manual_only', 'Manual Submission Only')
        ]
    )
    last_scanned_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp of latest parallel AI verification scan")
    scan_http_status = models.IntegerField(null=True, blank=True, help_text="Latest HTTP response code from live portal")
    source_last_checked = models.DateTimeField(default=timezone.now)
    
    shortlisted_by = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='shortlisted_opportunities')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Opportunities"
        ordering = ['deadline', '-created_at']

    def __str__(self):
        return f"{self.title} - {self.provider} ({self.country})"

    @property
    def is_deadline_passed(self):
        return timezone.now() > self.deadline

    @property
    def is_upcoming(self):
        if self.opening_date:
            return timezone.now() < self.opening_date
        return False

    @property
    def is_open(self):
        now = timezone.now()
        if self.opening_date and now < self.opening_date:
            return False
        return now <= self.deadline

    @property
    def days_remaining(self):
        delta = self.deadline - timezone.now()
        return max(0, delta.days)

    @property
    def days_until_opening(self):
        if self.opening_date and timezone.now() < self.opening_date:
            delta = self.opening_date - timezone.now()
            return max(0, delta.days)
        return 0

    @property
    def cycle_status(self):
        now = timezone.now()
        if self.opening_date and now < self.opening_date:
            return 'upcoming'
        if now > self.deadline:
            return 'closed'
        if self.days_remaining <= 14:
            return 'closing_soon'
        return 'open_now'

    @property
    def cycle_badge(self):
        status = self.cycle_status
        if status == 'upcoming':
            open_str = self.opening_date.strftime("%b %d, %Y") if self.opening_date else "Soon"
            days = self.days_until_opening
            return {
                'label': f'Opens in {days}d ({open_str})' if days > 0 else f'Opens {open_str}',
                'color': 'bg-blue-50 text-blue-700 border-blue-200',
                'status': 'upcoming'
            }
        elif status == 'closing_soon':
            return {
                'label': f'Closes in {self.days_remaining}d',
                'color': 'bg-red-50 text-red-700 border-red-200 animate-pulse',
                'status': 'closing_soon'
            }
        elif status == 'closed':
            return {
                'label': 'Cycle Closed',
                'color': 'bg-gray-100 text-gray-700 border-gray-300',
                'status': 'closed'
            }
        return {
            'label': 'Open for Applications',
            'color': 'bg-emerald-50 text-emerald-700 border-emerald-200',
            'status': 'open_now'
        }

    @property
    def urgency_badge(self):
        days = self.days_remaining
        if self.is_deadline_passed:
            return {'label': 'Deadline Passed', 'color': 'bg-gray-100 text-gray-700 border-gray-300'}
        elif days <= 7:
            return {'label': f'Due in {days}d', 'color': 'bg-red-50 text-red-700 border-red-200 animate-pulse'}
        elif days <= 30:
            return {'label': f'{days} days left', 'color': 'bg-amber-50 text-amber-700 border-amber-200'}
        return {'label': f'{days} days left', 'color': 'bg-emerald-50 text-emerald-700 border-emerald-200'}
