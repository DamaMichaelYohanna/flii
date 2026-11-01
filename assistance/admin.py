from django.contrib import admin
from .models import AssistancePackage, AssistanceBooking


@admin.register(AssistancePackage)
class AssistancePackageAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'category',
        'formatted_price_display',
        'price',
        'price_max',
        'currency',
        'delivery_type',
        'requires_human_review',
        'estimated_delivery_time',
        'is_active',
        'order',
    )
    list_filter = ('category', 'delivery_type', 'requires_human_review', 'is_active')
    search_fields = ('name', 'tagline', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('price', 'price_max', 'is_active', 'order')
    ordering = ('order', 'price')

    fieldsets = (
        ('Service Details', {
            'fields': ('name', 'slug', 'category', 'tagline', 'description', 'badge', 'icon', 'order', 'is_active')
        }),
        ('Pricing & Turnaround', {
            'fields': (('price', 'price_max', 'currency'), ('estimated_delivery_time', 'turnaround_days'), ('delivery_type', 'requires_human_review'))
        }),
        ('Requirements & Included Features', {
            'fields': ('service_instructions', 'document_requirements', 'features')
        }),
    )

    @admin.display(description='Catalogue Price')
    def formatted_price_display(self, obj):
        return obj.formatted_price


@admin.register(AssistanceBooking)
class AssistanceBookingAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'package_title', 'price', 'currency', 'status', 'payment_status', 'assigned_reviewer', 'created_at')
    list_filter = ('status', 'payment_status', 'urgency', 'assigned_reviewer', 'created_at')
    search_fields = ('order_number', 'user__email', 'user__first_name', 'user__last_name', 'package_title', 'target_scholarship', 'payment_reference')
    readonly_fields = ('order_number', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
