from django.contrib import admin
from .models import Story

@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'date_occurred', 'created_at')
    list_filter = ('category',)
    search_fields = ('title', 'situation', 'action', 'result', 'user__email')
