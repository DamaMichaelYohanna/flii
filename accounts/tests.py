from django.test import TestCase
from django.urls import reverse
from .models import User

class AccountTests(TestCase):
    def test_user_creation_and_auth(self):
        user = User.objects.create_user(
            username='testapplicant',
            email='test@example.com',
            password='Password123!',
            first_name='Test',
            last_name='Applicant'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertFalse(user.onboarding_completed)

    def test_landing_page_redirect_or_render(self):
        response = self.client.get(reverse('accounts:landing'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Stop searching.")

    def test_login_page_renders(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sign in to your application workspace")
        self.assertContains(response, "Continue with Google")

    def test_register_page_renders(self):
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Start your postgraduate journey")
        self.assertContains(response, "Sign up with Google")

    def test_google_oauth_service_provisioning(self):
        from .oauth import GoogleOAuthService
        oauth = GoogleOAuthService()
        google_info = {
            'email': 'new.scholar@gmail.com',
            'given_name': 'Amara',
            'family_name': 'Eze',
            'email_verified': True
        }
        user, created = oauth.get_or_create_user(google_info)
        self.assertTrue(created)
        self.assertEqual(user.email, 'new.scholar@gmail.com')
        self.assertEqual(user.first_name, 'Amara')
        self.assertTrue(user.is_email_verified)
        self.assertTrue(hasattr(user, 'applicant_profile'))

        # Existing user test
        user2, created2 = oauth.get_or_create_user(google_info)
        self.assertFalse(created2)
        self.assertEqual(user2.id, user.id)

    def test_google_login_sandbox_flow(self):
        response = self.client.get(reverse('accounts:google_login') + '?sandbox=1&email=test.google@example.com&name=Test+Google')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email='test.google@example.com').exists())

