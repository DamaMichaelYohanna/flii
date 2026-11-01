import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone


class SubscriptionPlan(models.Model):
    """
    Tiered subscription plan definition.
    Monthly: ₦3,000 | Three-Month Pass: ₦7,500 | Annual: ₦20,000 | Free: ₦0
    """
    TIER_CHOICES = [
        ('free', 'Free Tier'),
        ('premium', 'Premium Tier'),
    ]

    BILLING_CYCLE_CHOICES = [
        ('free', 'Free / No Billing'),
        ('monthly', 'Monthly Billing'),
        ('three_month', 'Three-Month Pass'),
        ('annual', 'Annual Billing'),
    ]

    name = models.CharField(max_length=100)
    plan_code = models.SlugField(max_length=50, unique=True, help_text="e.g. free, monthly, three_month, annual")
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='premium')
    billing_cycle = models.CharField(max_length=30, choices=BILLING_CYCLE_CHOICES, default='monthly')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=10, default='NGN')
    duration_days = models.PositiveIntegerField(
        default=30,
        help_text="Duration in days: 0 for free indefinite, 30 for monthly, 90 for 3-month, 365 for annual"
    )
    tagline = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    features_list = models.JSONField(
        default=list,
        help_text="List of feature bullet points to highlight on pricing page"
    )
    is_active = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'price']
        verbose_name = 'Subscription Plan'
        verbose_name_plural = 'Subscription Plans'

    def __str__(self):
        if self.price == Decimal('0.00'):
            return f"{self.name} (Free)"
        return f"{self.name} (₦{self.price:,.0f} {self.get_billing_cycle_display()})"

    @property
    def is_free(self):
        return self.tier == 'free' or self.price == Decimal('0.00')

    @property
    def is_premium(self):
        return self.tier == 'premium' and self.price > Decimal('0.00')

    @property
    def formatted_price(self):
        if self.is_free:
            return "Free"
        return f"₦{self.price:,.0f}"


class SubscriptionFeature(models.Model):
    """
    Catalog of features and capabilities governed by subscription entitlements.
    """
    FEATURE_TYPE_CHOICES = [
        ('boolean', 'Access Permission (True/False)'),
        ('numeric_limit', 'Numeric Usage Limit (e.g. max active applications)'),
    ]

    code = models.CharField(
        max_length=60,
        unique=True,
        help_text="Machine name, e.g. opportunity_discovery, active_applications, ai_writing_assistant"
    )
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    feature_type = models.CharField(max_length=20, choices=FEATURE_TYPE_CHOICES, default='boolean')
    default_limit_free = models.IntegerField(
        default=0,
        help_text="Default limit for Free users (-1 for unlimited, 0 for none/disabled)"
    )
    default_limit_premium = models.IntegerField(
        default=-1,
        help_text="Default limit for Premium users (-1 for unlimited)"
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Subscription Feature'
        verbose_name_plural = 'Subscription Features'

    def __str__(self):
        return f"{self.name} ({self.code})"


class PlanFeatureLimit(models.Model):
    """
    Explicit feature override / limit mapped to a specific SubscriptionPlan.
    """
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='plan_limits')
    feature = models.ForeignKey(SubscriptionFeature, on_delete=models.CASCADE, related_name='plan_limits')
    is_enabled = models.BooleanField(default=True)
    limit_value = models.IntegerField(
        default=-1,
        help_text="-1 = unlimited, 0 = disabled, >0 = maximum allowed instances"
    )

    class Meta:
        unique_together = ('plan', 'feature')
        verbose_name = 'Plan Feature Limit'
        verbose_name_plural = 'Plan Feature Limits'

    def __str__(self):
        val = "Unlimited" if self.limit_value == -1 else str(self.limit_value)
        return f"{self.plan.name} -> {self.feature.code}: {val}"


class Subscription(models.Model):
    """
    Active or historical user subscription record.
    Suggested statuses: Free, Active, Pending, Expired, Cancelled, Payment Failed.
    """
    STATUS_CHOICES = [
        ('free', 'Free'),
        ('active', 'Active'),
        ('pending', 'Pending'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('payment_failed', 'Payment Failed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='subscriptions'
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='free')
    billing_cycle = models.CharField(
        max_length=30,
        choices=SubscriptionPlan.BILLING_CYCLE_CHOICES,
        default='free'
    )
    start_date = models.DateTimeField(default=timezone.now)
    expiry_date = models.DateTimeField(null=True, blank=True)
    grace_period_days = models.PositiveIntegerField(
        default=3,
        help_text="Days after expiry where user retains access before hard cut-off"
    )
    auto_renew = models.BooleanField(default=False)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'

    def __str__(self):
        return f"{self.user.email} - {self.plan.name} [{self.get_status_display()}]"

    @property
    def is_active(self):
        if self.status == 'active':
            if self.expiry_date:
                # Check with grace period
                effective_expiry = self.expiry_date + timezone.timedelta(days=self.grace_period_days)
                return timezone.now() <= effective_expiry
            return True
        elif self.status == 'free':
            return True
        return False

    @property
    def is_premium(self):
        return self.is_active and self.plan.tier == 'premium' and self.status == 'active'

    @property
    def in_grace_period(self):
        if self.status == 'active' and self.expiry_date:
            now = timezone.now()
            return self.expiry_date < now <= (self.expiry_date + timezone.timedelta(days=self.grace_period_days))
        return False

    @property
    def days_remaining(self):
        if not self.expiry_date:
            return None
        delta = self.expiry_date - timezone.now()
        return max(0, delta.days)


class PaymentTransaction(models.Model):
    """
    Server-side record of financial transactions for subscriptions and service purchases.
    Adheres strictly to server verification and idempotency rules.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Payment Failed'),
        ('cancelled', 'Cancelled'),
        ('abandoned', 'Abandoned'),
    ]

    TRANSACTION_TYPE_CHOICES = [
        ('subscription', 'Subscription Plan'),
        ('service_order', 'Pay-Per-Application Service'),
    ]

    transaction_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payment_transactions'
    )
    transaction_type = models.CharField(
        max_length=30,
        choices=TRANSACTION_TYPE_CHOICES,
        default='subscription'
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    service_order_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="ID of linked ServiceOrder if payment for pay-per-application service"
    )
    reference = models.CharField(max_length=150, unique=True, db_index=True)
    provider = models.CharField(max_length=50, default='paystack')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default='NGN')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    gateway_response = models.JSONField(default=dict, blank=True)
    channel = models.CharField(max_length=50, blank=True, help_text="card, bank_transfer, ussd, mock")
    ip_address = models.CharField(max_length=60, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment Transaction'
        verbose_name_plural = 'Payment Transactions'

    def __str__(self):
        return f"[{self.get_status_display()}] {self.reference} - ₦{self.amount:,.2f} ({self.user.email})"

    @property
    def is_verified(self):
        return self.status == 'success'


class UserEntitlement(models.Model):
    """
    Direct user overrides or grants for specific features (e.g. trial access or manual admin override).
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='entitlement_overrides'
    )
    feature = models.ForeignKey(
        SubscriptionFeature,
        on_delete=models.CASCADE,
        related_name='user_overrides'
    )
    is_enabled = models.BooleanField(default=True)
    custom_limit = models.IntegerField(null=True, blank=True, help_text="-1 = unlimited, null = use plan default")
    valid_until = models.DateTimeField(null=True, blank=True)
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'feature')
        verbose_name = 'User Entitlement Override'
        verbose_name_plural = 'User Entitlement Overrides'

    def __str__(self):
        return f"{self.user.email} -> {self.feature.code}: enabled={self.is_enabled}"
