import logging
import uuid
from decimal import Decimal
from typing import Dict, Any, Tuple, Optional
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from .models import (
    SubscriptionPlan,
    SubscriptionFeature,
    PlanFeatureLimit,
    Subscription,
    PaymentTransaction,
)
from .providers import get_payment_provider, PaymentProviderError
from notifications.models import Notification

logger = logging.getLogger(__name__)


# Standard Default Plans adhering to user requirements
DEFAULT_PLANS = [
    {
        "name": "Free Tier",
        "plan_code": "free",
        "tier": "free",
        "billing_cycle": "free",
        "price": Decimal("0.00"),
        "duration_days": 0,
        "tagline": "Get started with 1 verified scholarship and core tracking.",
        "description": "Essential scholarship discovery. View 1 curated scholarship in full detail and track up to 2 active applications.",
        "features_list": [
            "View 1 verified scholarship opportunity in full detail",
            "Track up to 2 active scholarship applications",
            "Core Profile Fit score",
            "Standard Document Vault (25MB)",
            "5 AI preparation assistance credits / month",
            "Standard email & in-app deadline reminders"
        ],
        "is_popular": False,
        "order": 1,
    },
    {
        "name": "Monthly Premium",
        "plan_code": "monthly",
        "tier": "premium",
        "billing_cycle": "monthly",
        "price": Decimal("3000.00"),
        "duration_days": 30,
        "tagline": "Full access with flexible monthly billing.",
        "description": "Unlock unlimited opportunities, advanced profile-to-opportunity matching, and AI application writing assistance.",
        "features_list": [
            "Unlimited scholarship opportunity discovery",
            "Unlimited active application tracking",
            "Advanced personalised recommendations",
            "Detailed eligibility assessments",
            "Advanced profile-to-opportunity matching",
            "AI application writing assistance (Motivation, SOP, Proposal)",
            "Expanded Document Vault with secure access control",
            "Advanced deadline tracking and multi-stage reminders",
            "Application history and priority access to new features"
        ],
        "is_popular": False,
        "order": 2,
    },
    {
        "name": "Three-Month Pass",
        "plan_code": "three_month",
        "tier": "premium",
        "billing_cycle": "three_month",
        "price": Decimal("7500.00"),
        "duration_days": 90,
        "tagline": "Perfect for a full European or global admission cycle.",
        "description": "Save ₦1,500 compared to monthly. Uninterrupted premium access throughout your primary application deadlines.",
        "features_list": [
            "All Monthly Premium features included",
            "Full 90-day cycle coverage",
            "Save ₦1,500 over 3 months",
            "Unlimited scholarship opportunity discovery",
            "Unlimited active application tracking",
            "Advanced profile-to-opportunity matching",
            "Comprehensive AI application writing assistance",
            "Priority support queue"
        ],
        "is_popular": True,
        "order": 3,
    },
    {
        "name": "Annual Premium",
        "plan_code": "annual",
        "tier": "premium",
        "billing_cycle": "annual",
        "price": Decimal("20000.00"),
        "duration_days": 365,
        "tagline": "Maximum value for serious multi-country scholarship applicants.",
        "description": "Save ₦16,000 annually. Year-round scholarship intelligence, intake rolling deadlines, and mentorship perks.",
        "features_list": [
            "All Monthly Premium features included for 365 days",
            "Best value: Save ₦16,000 compared to monthly billing",
            "Unlimited scholarship opportunity discovery",
            "Unlimited active application tracking",
            "AI application writing assistance with highest priority throughput",
            "Expanded Document Vault with permanent archive",
            "Priority access to newly verified scholarship calls",
            "Priority review queue on pay-per-application services"
        ],
        "is_popular": False,
        "order": 4,
    },
]

DEFAULT_FEATURES = [
    {
        "code": "opportunity_discovery",
        "name": "Opportunity Discovery",
        "description": "Access to view curated scholarship opportunities in full.",
        "feature_type": "numeric_limit",
        "default_limit_free": 1,
        "default_limit_premium": -1,
    },
    {
        "code": "active_applications",
        "name": "Active Application Tracking",
        "description": "Number of concurrent applications tracked in workspace.",
        "feature_type": "numeric_limit",
        "default_limit_free": 2,
        "default_limit_premium": -1,
    },
    {
        "code": "advanced_matching",
        "name": "Advanced Profile-to-Opportunity Matching",
        "description": "Granular requirement analysis and fit diagnostics.",
        "feature_type": "boolean",
        "default_limit_free": 0,
        "default_limit_premium": -1,
    },
    {
        "code": "ai_writing_assistant",
        "name": "AI Application Writing Assistance",
        "description": "Grounded drafting for SOPs, motivation letters, and research proposals.",
        "feature_type": "boolean",
        "default_limit_free": 0,
        "default_limit_premium": -1,
    },
    {
        "code": "ai_writing_monthly",
        "name": "Monthly AI Generation Credits",
        "description": "Number of AI drafting queries per month.",
        "feature_type": "numeric_limit",
        "default_limit_free": 5,
        "default_limit_premium": -1,
    },
    {
        "code": "expanded_vault",
        "name": "Expanded Document Vault",
        "description": "Expanded storage limit and verification tracking for documents.",
        "feature_type": "boolean",
        "default_limit_free": 0,
        "default_limit_premium": -1,
    },
    {
        "code": "advanced_deadlines",
        "name": "Advanced Deadline Intelligence",
        "description": "30, 14, 7, 3, 1-day reminders and timezone-aware notifications.",
        "feature_type": "boolean",
        "default_limit_free": 0,
        "default_limit_premium": -1,
    },
]


class SubscriptionService:
    """
    Core subscription and billing management service.
    Enforces server-side verification, webhook idempotency, and clean lifecycle transitions.
    """

    @classmethod
    def seed_default_plans_and_features(cls):
        """
        Idempotently seeds default subscription plans, features, and plan limits.
        """
        for plan_data in DEFAULT_PLANS:
            SubscriptionPlan.objects.update_or_create(
                plan_code=plan_data["plan_code"],
                defaults=plan_data
            )

        for feat_data in DEFAULT_FEATURES:
            SubscriptionFeature.objects.update_or_create(
                code=feat_data["code"],
                defaults=feat_data
            )

        # Wire PlanFeatureLimits
        free_plan = SubscriptionPlan.objects.filter(plan_code='free').first()
        if free_plan:
            opp_feat = SubscriptionFeature.objects.filter(code='opportunity_discovery').first()
            if opp_feat:
                PlanFeatureLimit.objects.update_or_create(
                    plan=free_plan,
                    feature=opp_feat,
                    defaults={'is_enabled': True, 'limit_value': 1}
                )
            app_feat = SubscriptionFeature.objects.filter(code='active_applications').first()
            if app_feat:
                PlanFeatureLimit.objects.update_or_create(
                    plan=free_plan,
                    feature=app_feat,
                    defaults={'is_enabled': True, 'limit_value': 2}
                )

    @classmethod
    def get_or_create_free_subscription(cls, user) -> Subscription:
        """
        Ensures the user has at least a Free tier subscription record.
        """
        cls.seed_default_plans_and_features()
        free_plan = SubscriptionPlan.objects.filter(plan_code='free').first()

        existing = Subscription.objects.filter(user=user, status='free').first()
        if existing:
            return existing

        sub = Subscription.objects.create(
            user=user,
            plan=free_plan,
            status='free',
            billing_cycle='free',
            start_date=timezone.now(),
            expiry_date=None
        )
        return sub

    @classmethod
    def initialize_subscription_checkout(
        cls,
        user,
        plan_id: int,
        callback_url: str
    ) -> Dict[str, Any]:
        """
        Initiates a server-side payment transaction for a subscription plan.
        Never trusts client-provided amounts or parameters.
        """
        plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        if plan.is_free:
            raise ValueError("Free tier does not require payment processing.")

        provider = get_payment_provider()
        reference = f"FLII-SUB-{user.id}-{uuid.uuid4().hex[:10].upper()}"

        # 1. Create pending PaymentTransaction record server-side
        tx = PaymentTransaction.objects.create(
            user=user,
            transaction_type='subscription',
            reference=reference,
            provider='paystack' if hasattr(provider, 'secret_key') and provider.secret_key else 'test_sandbox',
            amount=plan.price,
            currency=plan.currency,
            status='pending',
            gateway_response={"plan_id": plan.id, "plan_code": plan.plan_code}
        )

        metadata = {
            "user_id": user.id,
            "user_email": user.email,
            "plan_id": plan.id,
            "plan_code": plan.plan_code,
            "transaction_type": "subscription",
            "transaction_db_id": str(tx.transaction_id),
        }

        # 2. Call gateway provider
        init_result = provider.initialize_transaction(
            email=user.email,
            amount=plan.price,
            reference=reference,
            callback_url=callback_url,
            metadata=metadata,
            currency=plan.currency
        )

        # Update gateway response
        tx.gateway_response = init_result.get("raw_response", {})
        tx.save(update_fields=['gateway_response', 'updated_at'])

        return {
            "authorization_url": init_result["authorization_url"],
            "reference": reference,
            "access_code": init_result.get("access_code"),
            "plan": plan,
            "transaction": tx,
        }

    @classmethod
    @transaction.atomic
    def verify_and_activate_subscription(cls, reference: str) -> Tuple[bool, str, Optional[Subscription]]:
        """
        Server-side transaction verification and idempotent activation.
        Rules:
        - Never trust frontend payment confirmation.
        - Verify transactions server-side.
        - Prevent duplicate subscription activation.
        - Store transaction references and payment records.
        """
        tx = PaymentTransaction.objects.filter(reference=reference).select_for_update().first()
        if not tx:
            logger.warning(f"Verification requested for unknown payment reference: {reference}")
            return False, "Invalid or unrecognized payment reference.", None

        # Idempotency check: if transaction is already marked success, do not reactivate
        if tx.status == 'success':
            logger.info(f"Transaction {reference} was already successfully verified and processed.")
            existing_sub = tx.subscription or Subscription.objects.filter(user=tx.user, status='active').first()
            return True, "Payment has already been confirmed and your subscription is active.", existing_sub

        # Call payment provider server-side verification
        provider = get_payment_provider()
        try:
            verification_result = provider.verify_transaction(reference)
        except PaymentProviderError as err:
            logger.error(f"Provider verification error for {reference}: {err}")
            tx.status = 'failed'
            tx.gateway_response = {"error": str(err)}
            tx.save(update_fields=['status', 'gateway_response', 'updated_at'])
            return False, f"Payment verification error: {str(err)}", None

        # Verify transaction status returned from gateway
        if not verification_result.get("is_success"):
            tx.status = 'failed'
            tx.gateway_response = verification_result.get("raw_response", {})
            tx.save(update_fields=['status', 'gateway_response', 'updated_at'])
            return False, "Payment was not successful or was cancelled by the user.", None

        # Update transaction record
        tx.status = 'success'
        tx.channel = verification_result.get("channel", "card")
        tx.paid_at = timezone.now()
        tx.gateway_response = verification_result.get("raw_response", {})

        # Identify target plan
        plan_id = None
        if isinstance(tx.gateway_response, dict):
            metadata = tx.gateway_response.get("metadata", {})
            if isinstance(metadata, dict):
                plan_id = metadata.get("plan_id")

        if not plan_id:
            # Fallback to amount-based plan resolution
            matched_plan = SubscriptionPlan.objects.filter(price=tx.amount, is_active=True).first()
        else:
            matched_plan = SubscriptionPlan.objects.filter(id=plan_id).first()

        if not matched_plan:
            matched_plan = SubscriptionPlan.objects.filter(plan_code='monthly').first()

        now = timezone.now()
        duration_days = matched_plan.duration_days if matched_plan else 30
        expiry_date = now + timezone.timedelta(days=duration_days)

        # Update or create active subscription
        # Expire any other active subscriptions for this user first
        Subscription.objects.filter(user=tx.user, status='active').update(
            status='expired',
            updated_at=now
        )

        sub = Subscription.objects.create(
            user=tx.user,
            plan=matched_plan,
            status='active',
            billing_cycle=matched_plan.billing_cycle,
            start_date=now,
            expiry_date=expiry_date,
            auto_renew=False
        )

        tx.subscription = sub
        tx.save(update_fields=['status', 'channel', 'paid_at', 'gateway_response', 'subscription', 'updated_at'])

        # Notify applicant
        Notification.objects.create(
            user=tx.user,
            title="✨ Premium Subscription Activated!",
            message=f"Your {matched_plan.name} is now active through {expiry_date.strftime('%B %d, %Y')}. Enjoy unlimited opportunity discovery, advanced matching, and AI assistance.",
            notification_type='system'
        )

        logger.info(f"Successfully activated {matched_plan.name} for user {tx.user.email} (ref: {reference})")
        return True, f"Payment confirmed! Welcome to {matched_plan.name}.", sub

    @classmethod
    def handle_paystack_webhook(
        cls,
        payload: Dict[str, Any],
        raw_body: bytes,
        signature_header: str
    ) -> Tuple[bool, str, int]:
        """
        Idempotent webhook handler with HMAC SHA512 signature verification.
        Does not activate subscriptions based solely on client redirect.
        """
        provider = get_payment_provider()

        # 1. Cryptographic signature check
        if not provider.verify_webhook_signature(raw_body, signature_header):
            logger.warning("Paystack webhook rejected: Invalid signature.")
            return False, "Invalid signature header", 400

        event_name = payload.get("event")
        data = payload.get("data", {})
        reference = data.get("reference")

        logger.info(f"Received Paystack webhook: event={event_name}, reference={reference}")

        if not reference:
            return False, "No reference in webhook payload", 400

        # Handle successful charge event
        if event_name in ["charge.success", "paymentrequest.success"]:
            # Check transaction type
            tx = PaymentTransaction.objects.filter(reference=reference).first()
            if not tx:
                logger.warning(f"Webhook received for unknown reference: {reference}")
                return False, "Reference not found in transactions", 404

            if tx.transaction_type == 'subscription':
                success, msg, sub = cls.verify_and_activate_subscription(reference)
                if success:
                    return True, "Subscription activated via webhook", 200
                else:
                    return False, msg, 400
            elif tx.transaction_type == 'service_order':
                from assistance.services import ServiceOrderService
                success, msg = ServiceOrderService.confirm_service_payment(reference)
                if success:
                    return True, "Service order marked paid via webhook", 200
                else:
                    return False, msg, 400

        return True, f"Webhook event '{event_name}' acknowledged", 200

    @classmethod
    def cancel_subscription(cls, user, reason: str = "") -> Tuple[bool, str]:
        """
        Cancels user's active subscription.
        User retains access until the end of their paid period.
        """
        sub = Subscription.objects.filter(user=user, status='active').first()
        if not sub:
            return False, "No active premium subscription found to cancel."

        sub.status = 'cancelled'
        sub.cancelled_at = timezone.now()
        sub.cancellation_reason = reason
        sub.auto_renew = False
        sub.save(update_fields=['status', 'cancelled_at', 'cancellation_reason', 'auto_renew', 'updated_at'])

        Notification.objects.create(
            user=user,
            title="Subscription Cancelled",
            message=f"Your subscription cancellation has been processed. You retain access until {sub.expiry_date.strftime('%b %d, %Y') if sub.expiry_date else 'expiry'}.",
            notification_type='system'
        )

        return True, "Your subscription has been cancelled. You will retain access until the end of your billing cycle."
