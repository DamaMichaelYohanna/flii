from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
import datetime
from accounts.models import User
from opportunities.models import Opportunity, OpportunitySource
from applications.models import Application


class DashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='regular_applicant',
            email='applicant@example.com',
            password='Password123!'
        )
        self.staff_user = User.objects.create_user(
            username='admin_staff',
            email='admin@example.com',
            password='Password123!',
            is_staff=True
        )
        self.opp = Opportunity.objects.create(
            title="German Research Grant",
            provider="DAAD",
            country="Germany",
            degree_level="masters",
            field_of_study="Computer Science",
            description="Fully funded grant",
            funding_type="fully_funded",
            funding_details="100% covered",
            eligibility_summary="Open to international graduates",
            application_url="https://daad.de",
            official_source_url="https://daad.de",
            deadline=timezone.now() + datetime.timedelta(days=45),
            status="active",
            verification_status="source_verified"
        )
        self.app = Application.objects.create(
            user=self.user,
            opportunity=self.opp,
            status='in_progress'
        )

    def test_applicant_dashboard(self):
        self.client.force_login(self.user)
        resp = self.client.get(reverse('dashboard:index'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "German Research Grant")

    def test_admin_system_dashboard_access(self):
        # Regular user should be redirected
        self.client.force_login(self.user)
        resp_denied = self.client.get(reverse('dashboard:admin_system_dashboard'), follow=True)
        self.assertContains(resp_denied, "Staff privileges required")

        # Staff user should be allowed
        self.client.force_login(self.staff_user)
        resp_allowed = self.client.get(reverse('dashboard:admin_system_dashboard'))
        self.assertEqual(resp_allowed.status_code, 200)
        self.assertContains(resp_allowed, "System Admin Command Center")
        self.assertContains(resp_allowed, "Total Users")
        self.assertContains(resp_allowed, "German Research Grant")

    def test_admin_users_view(self):
        self.client.force_login(self.staff_user)
        resp = self.client.get(reverse('dashboard:admin_users'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "applicant@example.com")
        self.assertContains(resp, "admin@example.com")

        # Test search query
        resp_search = self.client.get(reverse('dashboard:admin_users') + '?q=applicant')
        self.assertEqual(resp_search.status_code, 200)
        self.assertContains(resp_search, "applicant@example.com")

    def test_admin_toggle_user_staff(self):
        self.client.force_login(self.staff_user)
        self.assertFalse(self.user.is_staff)

        resp = self.client.get(
            reverse('dashboard:admin_toggle_user_staff', kwargs={'user_id': self.user.id}),
            follow=True
        )
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_staff)

        # Toggle back
        resp2 = self.client.get(
            reverse('dashboard:admin_toggle_user_staff', kwargs={'user_id': self.user.id}),
            follow=True
        )
        self.assertEqual(resp2.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_staff)

    def test_admin_applications_view(self):
        self.client.force_login(self.staff_user)
        resp = self.client.get(reverse('dashboard:admin_applications'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Global Applications Pipeline")
        self.assertContains(resp, "German Research Grant")
        self.assertContains(resp, "applicant@example.com")

    def test_admin_user_detail_view(self):
        self.client.force_login(self.staff_user)
        resp = self.client.get(reverse('dashboard:admin_user_detail', kwargs={'user_id': self.user.id}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "User Dossier")
        self.assertContains(resp, self.user.email)
        self.assertContains(resp, "German Research Grant")

    def test_admin_toggle_user_active(self):
        self.client.force_login(self.staff_user)
        self.assertTrue(self.user.is_active)

        resp = self.client.get(
            reverse('dashboard:admin_toggle_user_active', kwargs={'user_id': self.user.id}),
            follow=True
        )
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

        # Toggle back
        resp2 = self.client.get(
            reverse('dashboard:admin_toggle_user_active', kwargs={'user_id': self.user.id}),
            follow=True
        )
        self.assertEqual(resp2.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_admin_toggle_user_verified(self):
        self.client.force_login(self.staff_user)
        self.assertFalse(self.user.is_email_verified)

        resp = self.client.get(
            reverse('dashboard:admin_toggle_user_verified', kwargs={'user_id': self.user.id}),
            follow=True
        )
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)

    def test_admin_send_user_notification(self):
        self.client.force_login(self.staff_user)
        resp = self.client.post(
            reverse('dashboard:admin_send_user_notification', kwargs={'user_id': self.user.id}),
            {'title': 'Important Update', 'message': 'Please review your transcript.', 'action_url': '/vault/'},
            follow=True
        )
        self.assertEqual(resp.status_code, 200)
        from notifications.models import Notification
        notif = Notification.objects.filter(user=self.user, title='Important Update').first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.message, 'Please review your transcript.')
        self.assertEqual(notif.action_url, '/vault/')

    def test_admin_users_export_csv(self):
        self.client.force_login(self.staff_user)
        resp = self.client.get(reverse('dashboard:admin_users_export'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'text/csv')
        self.assertIn('attachment; filename="flii_users_export_', resp['Content-Disposition'])
        content = resp.content.decode('utf-8')
        self.assertIn('applicant@example.com', content)
        self.assertIn('admin@example.com', content)
