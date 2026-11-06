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
    slug = models.SlugField(max_length=280, unique=True, blank=True, null=True, help_text="SEO-friendly URL slug")
    image_url = models.URLField(max_length=500, blank=True, help_text="Thumbnail or featured hero image URL")
    image = models.ImageField(upload_to='opportunities/images/', blank=True, null=True, help_text="Optional uploaded featured image")
    is_featured = models.BooleanField(default=False, help_text="Pin as a top 3 hero featured scholarship")
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
    how_to_apply = models.TextField(blank=True, help_text="Step-by-step application instructions")
    
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

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            from django.utils.text import slugify
            base_slug = slugify(self.title)[:250]
            slug = base_slug
            counter = 1
            while Opportunity.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        if self.slug:
            return reverse('opportunities:detail_slug', kwargs={'slug': self.slug})
        return reverse('opportunities:detail', kwargs={'pk': self.pk})

    @property
    def display_image_url(self):
        if self.image:
            return self.image.url
        if self.image_url:
            return self.image_url
        country_lower = (self.country or '').lower()
        title_lower = (self.title or '').lower()
        if 'uk' in country_lower or 'united kingdom' in country_lower or 'oxford' in title_lower or 'chevening' in title_lower:
            return "https://images.unsplash.com/photo-1543872084-c7bd3822856f?q=80&w=800&auto=format&fit=crop"
        elif 'germany' in country_lower or 'daad' in title_lower:
            return "https://images.unsplash.com/photo-1527866512907-a35a62a7f673?q=80&w=800&auto=format&fit=crop"
        elif 'france' in country_lower:
            return "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?q=80&w=800&auto=format&fit=crop"
        elif 'europe' in country_lower or 'erasmus' in title_lower or 'intermaths' in title_lower:
            return "https://images.unsplash.com/photo-1467269204594-9661b134dd2b?q=80&w=800&auto=format&fit=crop"
        elif 'usa' in country_lower or 'united states' in country_lower or 'georgia' in title_lower:
            return "https://images.unsplash.com/photo-1541339907198-e08756dedf3f?q=80&w=800&auto=format&fit=crop"
        elif 'canada' in country_lower or 'victoria' in title_lower:
            return "https://images.unsplash.com/photo-1568792923760-d70635a89fa7?q=80&w=800&auto=format&fit=crop"
        elif 'australia' in country_lower:
            return "https://images.unsplash.com/photo-1523482580672-f109ba8cb9be?q=80&w=800&auto=format&fit=crop"
        elif 'china' in country_lower or 'shanghai' in title_lower or 'beijing' in title_lower:
            return "https://images.unsplash.com/photo-1508804185872-d7badad00f7d?q=80&w=800&auto=format&fit=crop"
        elif 'sweden' in country_lower or 'norway' in country_lower or 'denmark' in country_lower:
            return "https://images.unsplash.com/photo-1513622470522-26c3c8a854bc?q=80&w=800&auto=format&fit=crop"
        return "https://images.unsplash.com/photo-1523240795612-9a054b0db644?q=80&w=800&auto=format&fit=crop"


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
