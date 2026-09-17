from django.contrib import admin
from .models import Opportunity, OpportunitySource

@admin.register(OpportunitySource)
class OpportunitySourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'source_type', 'source_url', 'last_checked', 'last_verified')
    list_filter = ('source_type',)
    search_fields = ('name', 'source_url')


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ('title', 'provider', 'country', 'degree_level', 'funding_type', 'deadline', 'status', 'verification_status')
    list_filter = ('degree_level', 'funding_type', 'status', 'verification_status', 'country')
    search_fields = ('title', 'provider', 'country', 'field_of_study')
    readonly_fields = ('created_at', 'updated_at')
