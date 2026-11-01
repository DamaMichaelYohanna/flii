import logging
from typing import Dict, Any, Tuple, Optional
from django.utils import timezone
from django.conf import settings
from .models import (
    Subscription,
    SubscriptionPlan,
    SubscriptionFeature,
    PlanFeatureLimit,
    UserEntitlement,
)

logger = logging.getLogger(__name__)


class EntitlementService:
    """
    Centralised entitlement engine.
    Ensures business logic is never scattered across views.
    Enforces subscription plans, numeric limits, feature gates, and free tier restrictions.
    """

    @classmethod
    def get_active_subscription(cls, user) -> Optional[Subscription]:
        """
        Retrieves the user's currently active subscription.
        Checks validity including grace period.
        """
        if not user or not user.is_authenticated:
            return None

        # Look for active paid subscriptions first
        active_sub = Subscription.objects.filter(
            user=user,
            status='active'
        ).select_related('plan').first()

        if active_sub and active_sub.is_active:
            return active_sub

        # Fallback to free tier subscription
        free_sub = Subscription.objects.filter(
            user=user,
            status='free'
        ).select_related('plan').first()

        if free_sub:
            return free_sub

        # Auto-create free subscription if none exists
        from .services import SubscriptionService
        return SubscriptionService.get_or_create_free_subscription(user)

    @classmethod
    def has_active_subscription(cls, user) -> bool:
        """
        Returns True if the user has an active, valid Premium subscription.
        Staff and superusers automatically pass.
        """
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or user.is_staff:
            return True

        sub = cls.get_active_subscription(user)
        return sub is not None and sub.is_premium

    @classmethod
    def get_user_plan(cls, user) -> Optional[SubscriptionPlan]:
        """
        Returns the SubscriptionPlan currently governing the user.
        """
        sub = cls.get_active_subscription(user)
        if sub:
            return sub.plan
        return SubscriptionPlan.objects.filter(tier='free').first()

    @classmethod
    def can_access(cls, user, feature_code: str) -> bool:
        """
        Checks whether the user has access to a specific feature.
        Example: EntitlementService.can_access(user, "advanced_matching")
        """
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True

        now = timezone.now()

        # 1. Check for specific UserEntitlement override
        override = UserEntitlement.objects.filter(
            user=user,
            feature__code=feature_code
        ).first()
        if override:
            if override.valid_until is None or override.valid_until > now:
                return override.is_enabled

        # 2. Get user's plan
        sub = cls.get_active_subscription(user)
        plan = sub.plan if sub else None

        if not plan:
            plan = SubscriptionPlan.objects.filter(tier='free').first()

        if not plan:
            return False

        # 3. Check PlanFeatureLimit mapping
        plan_limit = PlanFeatureLimit.objects.filter(
            plan=plan,
            feature__code=feature_code
        ).first()

        if plan_limit:
            if not plan_limit.is_enabled:
                return False
            # If numeric limit, 0 means disabled, -1 means unlimited, >0 means allowed
            return plan_limit.limit_value != 0

        # 4. Fallback to SubscriptionFeature defaults
        feature = SubscriptionFeature.objects.filter(code=feature_code).first()
        if not feature:
            # If feature not in catalog yet, allow for premium, deny for free
            return cls.has_active_subscription(user)

        if plan.is_premium:
            return feature.default_limit_premium != 0
        return feature.default_limit_free != 0

    @classmethod
    def get_limit(cls, user, feature_code: str) -> int:
        """
        Retrieves the maximum allowed limit for a feature or resource.
        Returns:
            -1 for Unlimited
             0 for Disabled / None
            >0 for Specific numeric limit
        Example: EntitlementService.get_limit(user, "active_applications")
        """
        if not user or not user.is_authenticated:
            return 0
        if user.is_superuser:
            return -1

        now = timezone.now()

        # 1. Check UserEntitlement override
        override = UserEntitlement.objects.filter(
            user=user,
            feature__code=feature_code
        ).first()
        if override and (override.valid_until is None or override.valid_until > now):
            if override.custom_limit is not None:
                return override.custom_limit
            if not override.is_enabled:
                return 0

        # 2. Get user's plan
        sub = cls.get_active_subscription(user)
        plan = sub.plan if sub else None

        if not plan:
            plan = SubscriptionPlan.objects.filter(tier='free').first()

        if not plan:
            return 0

        # 3. Check PlanFeatureLimit mapping
        plan_limit = PlanFeatureLimit.objects.filter(
            plan=plan,
            feature__code=feature_code
        ).first()

        if plan_limit:
            if not plan_limit.is_enabled:
                return 0
            return plan_limit.limit_value

        # 4. Fallback to SubscriptionFeature defaults
        feature = SubscriptionFeature.objects.filter(code=feature_code).first()
        if feature:
            if plan.is_premium:
                return feature.default_limit_premium
            return feature.default_limit_free

        # Built-in sensible defaults matching specification
        if feature_code == "active_applications":
            return -1 if (plan and plan.is_premium) else 2
        elif feature_code == "opportunity_discovery":
            return -1 if (plan and plan.is_premium) else 1
        elif feature_code == "ai_writing_monthly":
            return -1 if (plan and plan.is_premium) else 5

        return -1 if (plan and plan.is_premium) else 0

    @classmethod
    def can_track_application(cls, user) -> Tuple[bool, int, int]:
        """
        Enforces: "Free users can track max of two applications. Premium users unlimited."
        Returns:
            (allowed: bool, current_active_count: int, max_limit: int)
        """
        if not user or not user.is_authenticated:
            return False, 0, 0
        if user.is_superuser or user.is_staff:
            return True, user.applications.count(), -1

        limit = cls.get_limit(user, "active_applications")
        # Exclude rejected/withdrawn from active count
        current_active = user.applications.exclude(status__in=['rejected', 'withdrawn']).count()

        if limit == -1:
            return True, current_active, -1

        can_add = current_active < limit
        return can_add, current_active, limit

    @classmethod
    def can_view_opportunity(cls, user, opportunity_id: int, request=None) -> Tuple[bool, Optional[str]]:
        """
        Enforces: "Free will only see so opportunity and can only view one.
        The second and any following will be blur out gradiently until transparent."
        Returns:
            (allowed: bool, reason: Optional[str])
        """
        if not user or not user.is_authenticated:
            return False, "Authentication required."
        if user.is_superuser or user.is_staff:
            return True, None
        if cls.has_active_subscription(user):
            return True, None

        # Free tier logic:
        # Check session or user state for the single allowed opportunity ID
        viewed_key = 'free_viewed_opportunity_id'
        if request and hasattr(request, 'session'):
            viewed_id = request.session.get(viewed_key)
            if viewed_id is None:
                # First opportunity viewed becomes the user's 1 free view
                request.session[viewed_key] = opportunity_id
                return True, None
            elif viewed_id == opportunity_id:
                # Re-visiting the same free opportunity is allowed
                return True, None
            else:
                return False, "Free accounts can view 1 verified scholarship. Upgrade to Premium for unlimited discovery."

        return True, None

    @classmethod
    def can_use_ai(cls, user, feature: str = "writing_assistant") -> Tuple[bool, str]:
        """
        Enforces AI usage limits: Free users have limited AI usage allowance (e.g. 5/mo),
        Premium users have unlimited / high monthly allowance.
        """
        if not user or not user.is_authenticated:
            return False, "Authentication required."
        if user.is_superuser or cls.has_active_subscription(user):
            return True, ""

        limit = cls.get_limit(user, "ai_writing_monthly")
        if limit == -1:
            return True, ""

        # Count AI usage in current month
        from agent_hub.models import AIAuditLog
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        usage_count = AIAuditLog.objects.filter(
            user=user,
            created_at__gte=start_of_month
        ).count()

        if usage_count >= limit:
            return False, f"You have reached your Free tier limit of {limit} AI generations this month. Upgrade to Premium for unlimited AI preparation assistance."
        return True, ""

    @classmethod
    def get_entitlements_summary(cls, user) -> Dict[str, Any]:
        """
        Returns structured dictionary of user's active entitlements for display in UI.
        """
        sub = cls.get_active_subscription(user)
        plan = sub.plan if sub else None
        is_premium = sub.is_premium if sub else False

        app_allowed, app_current, app_limit = cls.can_track_application(user)

        return {
            "is_premium": is_premium,
            "plan_name": plan.name if plan else "Free Tier",
            "plan_code": plan.plan_code if plan else "free",
            "billing_cycle": sub.get_billing_cycle_display() if sub else "Free",
            "expiry_date": sub.expiry_date if (sub and sub.expiry_date) else None,
            "days_remaining": sub.days_remaining if sub else None,
            "status": sub.get_status_display() if sub else "Free",
            "active_applications_limit": "Unlimited" if app_limit == -1 else app_limit,
            "active_applications_count": app_current,
            "can_track_more_applications": app_allowed,
            "unlimited_opportunity_discovery": is_premium,
            "ai_writing_assistant": is_premium or cls.can_access(user, "ai_writing_assistant"),
            "advanced_matching": is_premium or cls.can_access(user, "advanced_matching"),
            "document_vault_expanded": is_premium,
        }
