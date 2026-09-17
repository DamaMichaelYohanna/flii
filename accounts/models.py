from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    email = models.EmailField(unique=True, verbose_name="Email Address")
    is_email_verified = models.BooleanField(default=False, verbose_name="Email Verified")
    onboarding_completed = models.BooleanField(default=False, verbose_name="Onboarding Completed")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return f"{self.get_full_name() or self.username} <{self.email}>"
