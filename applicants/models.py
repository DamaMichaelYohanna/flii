from django.db import models
from django.conf import settings

class ApplicantProfile(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('non_binary', 'Non-Binary'),
        ('prefer_not_to_say', 'Prefer not to say'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applicant_profile')
    middle_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    country_of_origin = models.CharField(max_length=100, default='Nigeria')
    nationality = models.CharField(max_length=100, default='Nigerian')
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=30, choices=GENDER_CHOICES, blank=True)
    current_location = models.CharField(max_length=150, blank=True, help_text="City, Country (e.g. Lagos, Nigeria)")
    headline = models.CharField(max_length=255, blank=True, help_text="e.g. First-Class Computer Science Graduate | AI Researcher")
    bio_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.nationality})"

    @property
    def full_name(self):
        parts = [self.user.first_name, self.middle_name, self.user.last_name]
        return " ".join([p for p in parts if p]).strip() or self.user.username


class Education(models.Model):
    DEGREE_CHOICES = [
        ('bachelors', "Bachelor's Degree (BSc / BEng / BA)"),
        ('hnd', "Higher National Diploma (HND)"),
        ('masters', "Master's Degree (MSc / MEng / MA)"),
        ('doctorate', "Doctorate (PhD)"),
        ('diploma', "Postgraduate Diploma (PGD)"),
        ('other', "Other"),
    ]

    profile = models.ForeignKey(ApplicantProfile, on_delete=models.CASCADE, related_name='educations')
    institution = models.CharField(max_length=255)
    country = models.CharField(max_length=100, default='Nigeria')
    degree_level = models.CharField(max_length=50, choices=DEGREE_CHOICES, default='bachelors')
    field_of_study = models.CharField(max_length=200)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    graduation_year = models.IntegerField(null=True, blank=True)
    grade_classification = models.CharField(max_length=100, blank=True, help_text="e.g. First Class Honours, Second Class Upper (2:1)")
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, help_text="e.g. 4.85")
    max_cgpa = models.DecimalField(max_digits=4, decimal_places=2, default=5.00, help_text="e.g. 5.00 or 4.00")
    relevant_coursework = models.TextField(blank=True, help_text="Comma-separated or bullet points")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-graduation_year', '-end_date']

    def __str__(self):
        return f"{self.degree_level} in {self.field_of_study} - {self.institution}"


class Employment(models.Model):
    profile = models.ForeignKey(ApplicantProfile, on_delete=models.CASCADE, related_name='employments')
    organization = models.CharField(max_length=255)
    job_title = models.CharField(max_length=200)
    location = models.CharField(max_length=150, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    responsibilities = models.TextField(blank=True)
    achievements = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_current', '-start_date']

    def __str__(self):
        return f"{self.job_title} at {self.organization}"


class Skill(models.Model):
    CATEGORY_CHOICES = [
        ('technical', 'Technical / Engineering'),
        ('research', 'Research & Data Analysis'),
        ('domain', 'Domain Knowledge'),
        ('soft', 'Leadership & Communication'),
        ('tool', 'Tools & Frameworks'),
    ]

    profile = models.ForeignKey(ApplicantProfile, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='technical')
    proficiency = models.CharField(max_length=50, default='Advanced', blank=True)

    def __str__(self):
        return f"{self.name} ({self.category})"


class Project(models.Model):
    profile = models.ForeignKey(ApplicantProfile, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=255)
    description = models.TextField()
    role = models.CharField(max_length=150, blank=True)
    technologies = models.CharField(max_length=255, blank=True, help_text="e.g. Python, PyTorch, Django, React")
    outcome = models.TextField(blank=True, help_text="Measurable impact or key results")
    date = models.DateField(null=True, blank=True)
    project_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Achievement(models.Model):
    profile = models.ForeignKey(ApplicantProfile, on_delete=models.CASCADE, related_name='achievements')
    title = models.CharField(max_length=255)
    organization = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    date_awarded = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Certification(models.Model):
    profile = models.ForeignKey(ApplicantProfile, on_delete=models.CASCADE, related_name='certifications')
    title = models.CharField(max_length=255)
    issuer = models.CharField(max_length=255)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    credential_id = models.CharField(max_length=100, blank=True)
    credential_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.issuer}"


class ResearchExperience(models.Model):
    profile = models.OneToOneField(ApplicantProfile, on_delete=models.CASCADE, related_name='research_profile')
    research_interests = models.TextField(help_text="e.g. Machine Learning, NLP, Distributed Systems, Health Informatics")
    summary_experience = models.TextField(blank=True)
    publications = models.TextField(blank=True, help_text="Conference papers, journals, preprints, or undergraduate thesis")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Research Profile: {self.profile.full_name}"


class StudyGoal(models.Model):
    FUNDING_CHOICES = [
        ('fully_funded', 'Fully Funded Only (Tuition + Living Stipend + Travel)'),
        ('tuition_waiver', 'Tuition Waiver / Partial Scholarship'),
        ('self_funded', 'Self-Funded / Any'),
    ]

    profile = models.OneToOneField(ApplicantProfile, on_delete=models.CASCADE, related_name='study_goal')
    target_degree = models.CharField(max_length=100, default="Master's (MSc)")
    target_fields = models.CharField(max_length=255, help_text="e.g. Artificial Intelligence, Computer Science, Data Science")
    target_countries = models.CharField(max_length=255, help_text="e.g. Germany, United Kingdom, Sweden, Canada, USA")
    preferred_universities = models.TextField(blank=True)
    preferred_study_mode = models.CharField(max_length=50, default='Full-Time On-Campus')
    funding_preference = models.CharField(max_length=50, choices=FUNDING_CHOICES, default='fully_funded')
    intake_year = models.IntegerField(default=2026)
    career_goals = models.TextField(help_text="Short-term goals upon graduation")
    long_term_goals = models.TextField(help_text="Long-term vision (e.g. 5-10 years)")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Study Goals ({self.target_degree}) - {self.profile.full_name}"


class LanguageProficiency(models.Model):
    TEST_CHOICES = [
        ('none', 'No Test Taken (English Native / English Degree Medium)'),
        ('ielts', 'IELTS Academic'),
        ('toefl', 'TOEFL iBT'),
        ('duolingo', 'Duolingo English Test (DET)'),
        ('waec', 'WAEC / WASSCE English (C6 or better)'),
        ('other', 'Other Test'),
    ]

    profile = models.ForeignKey(ApplicantProfile, on_delete=models.CASCADE, related_name='languages')
    language = models.CharField(max_length=100, default='English')
    proficiency_level = models.CharField(max_length=100, default='Native / Bilingual')
    test_type = models.CharField(max_length=50, choices=TEST_CHOICES, default='none')
    overall_score = models.CharField(max_length=50, blank=True, help_text="e.g. 8.0, 110, 135")
    test_date = models.DateField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True, help_text="e.g. Medium of Instruction letter available")

    def __str__(self):
        return f"{self.language} ({self.proficiency_level})"
