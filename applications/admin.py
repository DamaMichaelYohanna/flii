from django.contrib import admin
from .models import Application, ApplicationRequirement, ApplicationTask

class ApplicationRequirementInline(admin.TabularInline):
    model = ApplicationRequirement
    extra = 0

class ApplicationTaskInline(admin.TabularInline):
    model = ApplicationTask
    extra = 0

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'opportunity', 'status', 'progress_percentage', 'created_at', 'updated_at')
    list_filter = ('status',)
    search_fields = ('user__email', 'opportunity__title')
    inlines = [ApplicationRequirementInline, ApplicationTaskInline]
