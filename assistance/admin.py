from django.contrib import admin
from .models import AssistancePackage, AssistanceBooking


@admin.register(AssistancePackage)
class AssistancePackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'service_type', 'price', 'currency', 'turnaround_days', 'badge', 'is_active', 'order')
    list_filter = ('service_type', 'is_active')
    search_fields = ('name', 'tagline', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('price', 'is_active', 'order')


@admin.register(AssistanceBooking)
class AssistanceBookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'package_title', 'service_type', 'price', 'currency', 'status', 'payment_status', 'created_at')
    list_filter = ('status', 'payment_status', 'service_type', 'urgency', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'package_title', 'target_scholarship', 'payment_reference')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
