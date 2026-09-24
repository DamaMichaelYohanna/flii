import math
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from django.urls import reverse

class PostCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    badge_color = models.CharField(max_length=100, default='bg-blue-50 text-blue-700 border-blue-200', help_text="Tailwind styling classes")
    icon = models.CharField(max_length=50, default='file-text', help_text="Lucide icon identifier")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Post Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Post(models.Model):
    STATUS_CHOICES = [
        ('published', 'Published (Live)'),
        ('draft', 'Draft (Admin Only)'),
        ('archived', 'Archived'),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='blog_posts')
    category = models.ForeignKey(PostCategory, on_delete=models.SET_NULL, null=True, related_name='posts')
    summary = models.TextField(help_text="Key summary / teaser for previews and cards")
    content = models.TextField(help_text="Full article body. Supports structured text, bullet points, and headers.")
    featured_image_url = models.URLField(max_length=500, blank=True, help_text="Optional cover image URL")
    is_breaking_news = models.BooleanField(default=False, help_text="Display prominent Breaking News badge and hero banner")
    is_pinned = models.BooleanField(default=False, help_text="Pin to top of blog homepage")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='published')
    published_at = models.DateTimeField(default=timezone.now)
    views_count = models.PositiveIntegerField(default=0)
    tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated keywords, e.g. Portugal, Visa, AIMA, Students")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-is_breaking_news', '-published_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)[:200]
            if not base_slug:
                base_slug = "post"
            slug = base_slug
            counter = 1
            while Post.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:detail', kwargs={'slug': self.slug})

    @property
    def reading_time(self):
        """Calculates estimated reading time in minutes assuming 200 words/min."""
        total_words = len(self.content.split())
        return max(1, math.ceil(total_words / 200))

    @property
    def tag_list(self):
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(',') if t.strip()]

    @property
    def clean_content(self):
        """Returns body content stripped of markdown symbols (hashes, asterisks, rule lines)."""
        import re
        text = self.content or ""
        # Remove headers like ### or ##
        text = re.sub(r'^[ \t]*#{1,6}[ \t]*', '', text, flags=re.MULTILINE)
        # Remove horizontal rules (--- or *** or ___)
        text = re.sub(r'^[ \t]*[-*_]{3,}[ \t]*$', '', text, flags=re.MULTILINE)
        # Remove bold / italic markdown markers (**text**, *text*, __text__, _text_)
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'__(.*?)__', r'\1', text)
        return text.strip()
