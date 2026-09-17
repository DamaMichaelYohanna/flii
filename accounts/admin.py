from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_email_verified', 'onboarding_completed', 'is_staff', 'created_at')
    list_filter = ('is_email_verified', 'onboarding_completed', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name', 'username')
    ordering = ('-created_at',)
