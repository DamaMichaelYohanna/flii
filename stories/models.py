from django.db import models
from django.conf import settings

class Story(models.Model):
    CATEGORY_CHOICES = [
        ('leadership', 'Leadership & Initiative'),
        ('academic', 'Academic Achievement & Excellence'),
        ('community', 'Community Impact & Social Change'),
        ('entrepreneurship', 'Entrepreneurship & Problem Solving'),
        ('problem_solving', 'Technical & Analytical Problem Solving'),
        ('failure_resilience', 'Failure, Resilience & Growth'),
        ('teamwork', 'Teamwork & Cross-Cultural Collaboration'),
        ('innovation', 'Innovation & Creativity'),
        ('career', 'Career & Professional Milestone'),
        ('research', 'Research Breakthrough & Investigation'),
        ('volunteering', 'Volunteering & Mentorship'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='stories')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='leadership')
    title = models.CharField(max_length=255, help_text="A memorable headline for this experience")
    situation = models.TextField(help_text="Context: Where, when, and what was the background?")
    challenge = models.TextField(help_text="Obstacle: What was the specific problem or bottleneck?")
    action = models.TextField(help_text="Action: What specific steps did you take? What was your direct role?")
    result = models.TextField(help_text="Outcome: What was the measurable result, impact, or metric?")
    lesson_learned = models.TextField(help_text="Key takeaway, personal growth, and self-reflection")
    skills_demonstrated = models.CharField(max_length=255, help_text="e.g. Strategic Planning, Python, Stakeholder Management")
    date_occurred = models.DateField(null=True, blank=True)
    supporting_evidence = models.TextField(blank=True, help_text="Links, repos, news mentions, or certificate references")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Stories"
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_category_display()}] {self.title}"
