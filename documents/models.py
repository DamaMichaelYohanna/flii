import os
from django.db import models
from django.conf import settings

def user_document_upload_path(instance, filename):
    # Secure user-isolated upload path
    return f"vault/user_{instance.user.id}/{instance.document_type}/{filename}"

class Document(models.Model):
    DOCUMENT_TYPES = [
        ('cv', 'Curriculum Vitae (CV) / Resume'),
        ('transcript', 'Official Academic Transcript'),
        ('degree_certificate', 'Degree Certificate / Statement of Result'),
        ('passport', 'International Passport Data Page'),
        ('recommendation_letter', 'Letter of Recommendation'),
        ('certificate', 'Professional Certification / Award'),
        ('portfolio', 'Portfolio / Research Proposal / Writing Sample'),
        ('english_test', 'English Proficiency Result / Medium of Instruction'),
        ('other', 'Other Supporting Document'),
    ]

    VERIFICATION_STATUSES = [
        ('unverified', 'Uploaded (Self-Declared)'),
        ('verified', 'Verified / Validated'),
        ('needs_update', 'Needs Update / Expiring Soon'),
        ('expired', 'Expired'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=255, help_text="e.g. Unilag Official Transcript (Undergraduate)")
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES, default='cv')
    file = models.FileField(upload_to=user_document_upload_path)
    file_size_bytes = models.BigIntegerField(default=0)
    file_format = models.CharField(max_length=20, blank=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    expiration_date = models.DateField(null=True, blank=True, help_text="Applicable for Passports, English Tests, Certifications")
    verification_status = models.CharField(max_length=30, choices=VERIFICATION_STATUSES, default='unverified')
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-upload_date']

    def __str__(self):
        return f"{self.title} ({self.get_document_type_display()})"

    def save(self, *args, **kwargs):
        if self.file and hasattr(self.file, 'size') and not self.file_size_bytes:
            self.file_size_bytes = self.file.size
        if self.file and not self.file_format:
            ext = os.path.splitext(self.file.name)[1].lower().replace('.', '')
            self.file_format = ext
        super().save(*args, **kwargs)

    @property
    def formatted_size(self):
        bytes_val = self.file_size_bytes or 0
        if bytes_val < 1024:
            return f"{bytes_val} B"
        elif bytes_val < 1024 * 1024:
            return f"{bytes_val / 1024:.1f} KB"
        return f"{bytes_val / (1024 * 1024):.1f} MB"
