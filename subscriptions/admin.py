from django.contrib import admin
from .models import (
    SubscriptionPlan,
    SubscriptionFeature,
    PlanFeatureLimit,
    Subscription,
    PaymentTransaction,
    UserEntitlement,
)


class PlanFeatureLimitInline(admin.TabularInline):
    model = PlanFeatureLimit
    extra = 1


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'plan_code', 'tier', 'billing_cycle', 'price', 'duration_days', 'is_active', 'is_popular', 'order')
    list_filter = ('tier', 'billing_cycle', 'is_active', 'is_popular')
    search_fields = ('name', 'plan_code', 'tagline')
    inlines = [PlanFeatureLimitInline]
    ordering = ('order', 'price')


@admin.register(SubscriptionFeature)
class SubscriptionFeatureAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'feature_type', 'default_limit_free', 'default_limit_premium')
    search_fields = ('name', 'code', 'description')
    list_filter = ('feature_type',)


@admin.register(PlanFeatureLimit)
class PlanFeatureLimitAdmin(admin.ModelAdmin):
    list_display = ('plan', 'feature', 'is_enabled', 'limit_value')
    list_filter = ('plan', 'is_enabled')
    search_fields = ('plan__name', 'feature__name', 'feature__code')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'status', 'billing_cycle', 'start_date', 'expiry_date', 'is_active')
    list_filter = ('status', 'billing_cycle', 'plan__tier')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'plan__name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('reference', 'user', 'transaction_type', 'amount', 'currency', 'status', 'provider', 'channel', 'paid_at', 'created_at')
    list_filter = ('status', 'transaction_type', 'provider', 'currency')
    search_fields = ('reference', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('transaction_id', 'created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(UserEntitlement)
class UserEntitlementAdmin(admin.ModelAdmin):
    list_display = ('user', 'feature', 'is_enabled', 'custom_limit', 'valid_until', 'reason')
    list_filter = ('is_enabled', 'feature')
    search_fields = ('user__email', 'feature__name', 'feature__code')
