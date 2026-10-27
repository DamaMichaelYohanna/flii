from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
import datetime

from accounts.models import User
from assistance.models import AssistancePackage, AssistanceBooking
from assistance.services import ensure_default_packages_seeded
from notifications.models import Notification
from opportunities.models import Opportunity
from applications.models import Application


class AssistanceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='applicant_test',
            email='applicant@example.com',
            password='TestPassword123!',
            first_name='Amara',
            last_name='Eze'
        )
        self.staff_user = User.objects.create_user(
            username='admin_test',
            email='mentor@flii.org',
            password='TestPassword123!',
            is_staff=True,
            first_name='Admin',
            last_name='Mentor'
        )
        ensure_default_packages_seeded()
        self.package = AssistancePackage.objects.first()

        self.opp = Opportunity.objects.create(
            title="Erasmus Mundus BDMA",
            provider="European Commission",
            country="Belgium",
            deadline=timezone.now() + datetime.timedelta(days=60)
        )
        self.app = Application.objects.create(
            user=self.user,
            opportunity=self.opp,
            status='preparing'
        )

    def test_assistance_home_view(self):
        from django.utils.html import escape
        response = self.client.get(reverse('assistance:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, escape(self.package.name))
        self.assertContains(response, "Admissions-grade guidance")

    def test_book_assistance_get(self):
        from django.utils.html import escape
        self.client.force_login(self.user)
        response = self.client.get(reverse('assistance:book'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Request Paid Admin Assistance")
        self.assertContains(response, escape(self.package.name))

    def test_book_assistance_post_success(self):
        self.client.force_login(self.user)
        payload = {
            'package_id': self.package.id,
            'application_id': self.app.id,
            'target_scholarship': 'Erasmus Mundus BDMA',
            'target_university': 'ULB Brussels',
            'urgency': 'standard',
            'preferred_time_slot': 'afternoon',
            'applicant_notes': 'Please audit my personal statement leadership narrative.',
            'preferred_contact_method': 'google_meet',
            'contact_phone': '+234 800 000 0000',
        }
        response = self.client.post(reverse('assistance:book'), payload)
        self.assertEqual(response.status_code, 302)

        booking = AssistanceBooking.objects.filter(user=self.user).first()
        self.assertIsNotNone(booking)
        self.assertEqual(booking.package_title, self.package.name)
        self.assertEqual(booking.price, self.package.price)
        self.assertEqual(booking.status, 'pending_payment')
        self.assertEqual(booking.payment_status, 'unpaid')
        self.assertEqual(booking.application, self.app)

        # Check notifications generated
        self.assertTrue(Notification.objects.filter(user=self.user, title__icontains="Assistance Booked").exists())
        self.assertTrue(Notification.objects.filter(user=self.staff_user, title__icontains="New Paid Assistance").exists())

    def test_urgency_price_multipliers(self):
        self.client.force_login(self.user)

        # Priority (+25%)
        resp_prio = self.client.post(reverse('assistance:book'), {
            'package_id': self.package.id,
            'target_scholarship': 'DAAD EPOS',
            'urgency': 'priority',
            'applicant_notes': 'Urgent 48h review',
        })
        self.assertEqual(resp_prio.status_code, 302)
        prio_booking = AssistanceBooking.objects.filter(urgency='priority').first()
        expected_prio_price = (self.package.price * Decimal('1.25')).quantize(Decimal('0.01'))
        self.assertEqual(prio_booking.price, expected_prio_price)

        # Rush (+50%)
        resp_rush = self.client.post(reverse('assistance:book'), {
            'package_id': self.package.id,
            'target_scholarship': 'Chevening',
            'urgency': 'rush',
            'applicant_notes': 'Rush 24h review',
        })
        self.assertEqual(resp_rush.status_code, 302)
        rush_booking = AssistanceBooking.objects.filter(urgency='rush').first()
        expected_rush_price = (self.package.price * Decimal('1.50')).quantize(Decimal('0.01'))
        self.assertEqual(rush_booking.price, expected_rush_price)

    def test_payment_reference_submission(self):
        booking = AssistanceBooking.objects.create(
            user=self.user,
            package=self.package,
            package_title=self.package.name,
            service_type=self.package.service_type,
            price=self.package.price,
            applicant_notes="Need feedback on essay",
            contact_email=self.user.email,
            status='pending_payment',
            payment_status='unpaid'
        )

        self.client.force_login(self.user)
        resp = self.client.post(reverse('assistance:booking_payment_submit', kwargs={'pk': booking.id}), {
            'payment_reference': 'WIRE-2026-9988'
        })
        self.assertEqual(resp.status_code, 302)

        booking.refresh_from_db()
        self.assertEqual(booking.payment_reference, 'WIRE-2026-9988')
        self.assertEqual(booking.payment_status, 'pending_verification')

    def test_my_bookings_view(self):
        AssistanceBooking.objects.create(
            user=self.user,
            package=self.package,
            package_title=self.package.name,
            service_type=self.package.service_type,
            price=self.package.price,
            applicant_notes="Test notes",
            contact_email=self.user.email
        )
        from django.utils.html import escape
        self.client.force_login(self.user)
        response = self.client.get(reverse('assistance:my_bookings'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, escape(self.package.name))

    def test_admin_hub_permissions_and_fulfillment(self):
        booking = AssistanceBooking.objects.create(
            user=self.user,
            package=self.package,
            package_title=self.package.name,
            service_type='advisory_call',
            price=self.package.price,
            applicant_notes="Live advisory request",
            contact_email=self.user.email,
            status='pending_payment',
            payment_status='unpaid'
        )

        # Regular user denied
        self.client.force_login(self.user)
        resp_denied = self.client.get(reverse('assistance:admin_hub'), follow=True)
        self.assertContains(resp_denied, "Staff privileges required")

        # Staff user allowed
        self.client.force_login(self.staff_user)
        resp_allowed = self.client.get(reverse('assistance:admin_hub'))
        self.assertEqual(resp_allowed.status_code, 200)
        self.assertContains(resp_allowed, self.user.email)

        # Staff fulfills booking (Sets scheduled call and meeting link)
        scheduled_time = (timezone.now() + datetime.timedelta(days=2)).replace(microsecond=0)
        scheduled_iso = scheduled_time.strftime('%Y-%m-%dT%H:%M')
        resp_update = self.client.post(reverse('assistance:admin_booking_detail', kwargs={'pk': booking.id}), {
            'status': 'scheduled',
            'payment_status': 'paid',
            'meeting_link': 'https://meet.google.com/test-meet-123',
            'scheduled_at': scheduled_iso,
            'deliverable_feedback': 'We will review your SOP draft and discuss research goals during the call.',
            'admin_notes': 'Confirmed payment via bank transfer.'
        })
        self.assertEqual(resp_update.status_code, 302)

        booking.refresh_from_db()
        self.assertEqual(booking.status, 'scheduled')
        self.assertEqual(booking.payment_status, 'paid')
        self.assertEqual(booking.meeting_link, 'https://meet.google.com/test-meet-123')
        self.assertEqual(booking.assigned_admin, self.staff_user)

        # Applicant notified of scheduled call
        self.assertTrue(Notification.objects.filter(
            user=self.user,
            title__icontains="Live Session Scheduled"
        ).exists())
