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

    def test_register_page_renders(self):
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Start your postgraduate journey")
