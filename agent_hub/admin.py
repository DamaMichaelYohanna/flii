from django.contrib import admin
from .models import AgentAction, AIAuditLog

@admin.register(AgentAction)
class AgentActionAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'action_type', 'status', 'created_at', 'resolved_at')
    list_filter = ('action_type', 'status')
    search_fields = ('title', 'user__email', 'description')


@admin.register(AIAuditLog)
class AIAuditLogAdmin(admin.ModelAdmin):
    list_display = ('action_type', 'user', 'provider', 'status', 'created_at')
    list_filter = ('action_type', 'provider', 'status')
    search_fields = ('summary', 'user__email', 'input_ref')
