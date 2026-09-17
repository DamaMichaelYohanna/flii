from django.contrib import admin
from .models import Document

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'document_type', 'verification_status', 'formatted_size', 'upload_date')
    list_filter = ('document_type', 'verification_status')
    search_fields = ('title', 'user__email')
