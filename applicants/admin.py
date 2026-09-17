from django.contrib import admin
from .models import (
    ApplicantProfile, Education, Employment, Skill, Project,
    Achievement, Certification, ResearchExperience, StudyGoal, LanguageProficiency
)

class EducationInline(admin.TabularInline):
    model = Education
    extra = 0

class EmploymentInline(admin.TabularInline):
    model = Employment
    extra = 0

@admin.register(ApplicantProfile)
class ApplicantProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'nationality', 'country_of_origin', 'current_location', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'nationality')
    inlines = [EducationInline, EmploymentInline]
