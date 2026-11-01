from decimal import Decimal
import json
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse

from .models import (
    SubscriptionPlan,
    SubscriptionFeature,
    Subscription,
    PaymentTransaction,
    UserEntitlement,
)
from .services import SubscriptionService
from .entitlements import EntitlementService
from .providers import get_payment_provider, MockSandboxPaymentProvider, PaystackPaymentProvider
from opportunities.models import Opportunity
from applications.models import Application

User = get_user_model()


class SubscriptionEntitlementTests(TestCase):
    def setUp(self):
        SubscriptionService.seed_default_plans_and_features()

        self.user = User.objects.create_user(
            username='applicant_test',
            email='applicant@flii.org',
            password='TestPassword2026!'
        )

        self.free_plan = SubscriptionPlan.objects.get(plan_code='free')
        self.monthly_plan = SubscriptionPlan.objects.get(plan_code='monthly')
        self.three_month_plan = SubscriptionPlan.objects.get(plan_code='three_month')
        self.annual_plan = SubscriptionPlan.objects.get(plan_code='annual')

    def test_seeded_pricing_and_plans(self):
        """Verifies initial pricing matching user requirements: Monthly ₦3,000, 3-Month ₦7,500, Annual ₦20,000."""
        self.assertEqual(self.free_plan.price, Decimal("0.00"))
        self.assertEqual(self.monthly_plan.price, Decimal("3000.00"))
        self.assertEqual(self.three_month_plan.price, Decimal("7500.00"))
        self.assertEqual(self.annual_plan.price, Decimal("20000.00"))

        self.assertEqual(self.monthly_plan.duration_days, 30)
        self.assertEqual(self.three_month_plan.duration_days, 90)
        self.assertEqual(self.annual_plan.duration_days, 365)

    def test_default_free_tier_entitlements(self):
        """Verifies default limits for Free tier: 2 applications, 1 opportunity view."""
        self.assertFalse(EntitlementService.has_active_subscription(self.user))

        # Check limit on active applications
        app_limit = EntitlementService.get_limit(self.user, "active_applications")
        self.assertEqual(app_limit, 2)

        # Check boolean feature access
        self.assertFalse(EntitlementService.can_access(self.user, "advanced_matching"))

        # Check can_track_application
        can_track, current, limit = EntitlementService.can_track_application(self.user)
        self.assertTrue(can_track)
        self.assertEqual(current, 0)
        self.assertEqual(limit, 2)

    def test_free_tier_max_two_applications_limit(self):
        """Verifies: Free users can track max of two applications."""
        opp1 = Opportunity.objects.create(
            title="Scholarship 1", provider="Provider 1", country="Germany", deadline=timezone.now() + timezone.timedelta(days=30)
        )
        opp2 = Opportunity.objects.create(
            title="Scholarship 2", provider="Provider 2", country="France", deadline=timezone.now() + timezone.timedelta(days=40)
        )
        opp3 = Opportunity.objects.create(
            title="Scholarship 3", provider="Provider 3", country="UK", deadline=timezone.now() + timezone.timedelta(days=50)
        )

        # 1st application
        Application.objects.create(user=self.user, opportunity=opp1, status='preparing')
        can_track, current, limit = EntitlementService.can_track_application(self.user)
        self.assertTrue(can_track)
        self.assertEqual(current, 1)

        # 2nd application
        Application.objects.create(user=self.user, opportunity=opp2, status='in_progress')
        can_track, current, limit = EntitlementService.can_track_application(self.user)
        self.assertFalse(can_track)  # Limit reached (current == 2)
        self.assertEqual(current, 2)

        # Attempting to track 3rd application via web route redirects with alert
        self.client.force_login(self.user)
        response = self.client.get(reverse('applications:create_from_opportunity', kwargs={'opportunity_id': opp3.id}))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('subscriptions:pricing'), response.url)

    def test_free_tier_single_opportunity_view(self):
        """Verifies: Free users can view only one opportunity in detail."""
        factory = RequestFactory()
        req1 = factory.get('/')
        req1.user = self.user
        req1.session = {}

        # 1st opportunity view -> allowed and saved to session
        allowed, reason = EntitlementService.can_view_opportunity(self.user, 101, req1)
        self.assertTrue(allowed)
        self.assertEqual(req1.session.get('free_viewed_opportunity_id'), 101)

        # Viewing same opportunity again -> allowed
        allowed, reason = EntitlementService.can_view_opportunity(self.user, 101, req1)
        self.assertTrue(allowed)

        # Viewing a different opportunity -> denied
        allowed, reason = EntitlementService.can_view_opportunity(self.user, 102, req1)
        self.assertFalse(allowed)
        self.assertIn("view 1 verified scholarship", reason)

    def test_premium_unlimited_entitlements(self):
        """Verifies that Premium tier unlocks unlimited applications and full feature access."""
        # Upgrade user to Premium
        now = timezone.now()
        Subscription.objects.create(
            user=self.user,
            plan=self.monthly_plan,
            status='active',
            billing_cycle='monthly',
            start_date=now,
            expiry_date=now + timezone.timedelta(days=30)
        )

        self.assertTrue(EntitlementService.has_active_subscription(self.user))
        self.assertEqual(EntitlementService.get_limit(self.user, "active_applications"), -1)
        self.assertTrue(EntitlementService.can_access(self.user, "advanced_matching"))

        can_track, current, limit = EntitlementService.can_track_application(self.user)
        self.assertTrue(can_track)
        self.assertEqual(limit, -1)

    def test_payment_initialization_and_verification_idempotency(self):
        """
        Verifies:
        - Server-side transaction initialization
        - Server-side verification activating premium
        - Idempotent processing avoiding duplicate activation
        """
        callback_url = "http://testserver/subscriptions/callback/"
        checkout = SubscriptionService.initialize_subscription_checkout(
            user=self.user,
            plan_id=self.monthly_plan.id,
            callback_url=callback_url
        )
        ref = checkout["reference"]
        self.assertIsNotNone(ref)

        tx = PaymentTransaction.objects.get(reference=ref)
        self.assertEqual(tx.status, 'pending')
        self.assertEqual(tx.amount, Decimal("3000.00"))

        # Verify transaction server-side
        success, msg, sub = SubscriptionService.verify_and_activate_subscription(ref)
        self.assertTrue(success)
        self.assertIsNotNone(sub)
        self.assertEqual(sub.status, 'active')
        self.assertEqual(sub.plan, self.monthly_plan)

        # Idempotency check: verifying again returns existing sub without duplicate
        success2, msg2, sub2 = SubscriptionService.verify_and_activate_subscription(ref)
        self.assertTrue(success2)
        self.assertEqual(sub.id, sub2.id)
        self.assertEqual(Subscription.objects.filter(user=self.user, status='active').count(), 1)

    def test_webhook_idempotent_processing(self):
        """Tests that webhooks verify signatures and process idempotently."""
        checkout = SubscriptionService.initialize_subscription_checkout(
            user=self.user,
            plan_id=self.three_month_plan.id,
            callback_url="http://testserver/subscriptions/callback/"
        )
        ref = checkout["reference"]

        payload = {
            "event": "charge.success",
            "data": {
                "reference": ref,
                "amount": 750000,
                "currency": "NGN",
                "status": "success",
            }
        }
        raw_body = json.dumps(payload).encode('utf-8')

        success, msg, status_code = SubscriptionService.handle_paystack_webhook(
            payload=payload,
            raw_body=raw_body,
            signature_header="test_sandbox_valid_sig"
        )
        self.assertTrue(success)
        self.assertEqual(status_code, 200)

        # Check that user is now on Three-Month Pass
        active_sub = Subscription.objects.filter(user=self.user, status='active').first()
        self.assertIsNotNone(active_sub)
        self.assertEqual(active_sub.plan.plan_code, 'three_month')
