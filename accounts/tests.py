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
        self.assertContains(response, "Make your next")

    def test_login_page_renders(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sign in to your application workspace")
        self.assertContains(response, "Continue with Google")
        self.assertContains(response, "Forgot password?")
        self.assertContains(response, reverse('accounts:password_reset'))
        self.assertContains(response, reverse('accounts:register'))
        self.assertContains(response, "Register for free")

    def test_register_page_renders(self):
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Start your postgraduate journey")
        self.assertContains(response, "Sign up with Google")
        self.assertContains(response, reverse('accounts:login'))
        self.assertContains(response, "Sign in to your workspace")

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

    def test_password_reset_views_and_full_flow(self):
        from django.core import mail
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        from django.contrib.auth.tokens import default_token_generator

        # 1. Create a user to test password reset
        user = User.objects.create_user(
            username='reset_user',
            email='reset_user@example.com',
            password='OldPassword123!'
        )

        # 2. Test password reset request view renders
        response = self.client.get(reverse('accounts:password_reset'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reset your password")
        self.assertContains(response, "Registered Email Address")

        # 3. Test submitting email sends password reset link
        post_response = self.client.post(reverse('accounts:password_reset'), {
            'email': 'reset_user@example.com'
        })
        self.assertRedirects(post_response, reverse('accounts:password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['reset_user@example.com'])
        self.assertIn("Reset your Flii Workspace password", email.subject)
        self.assertIn("password-reset-confirm", email.body)

        # 4. Test password reset done page renders
        done_response = self.client.get(reverse('accounts:password_reset_done'))
        self.assertEqual(done_response.status_code, 200)
        self.assertContains(done_response, "Check your inbox")

        # 5. Test password reset confirm view renders with valid token
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        confirm_url = reverse('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
        
        confirm_response = self.client.get(confirm_url, follow=True)
        self.assertEqual(confirm_response.status_code, 200)
        self.assertContains(confirm_response, "Set a new password")

        # 6. Test submitting new password updates user password and redirects to complete
        new_password = "BrandNewPassword2026!"
        submit_new_pass_response = self.client.post(confirm_response.request['PATH_INFO'], {
            'new_password1': new_password,
            'new_password2': new_password,
        })
        self.assertRedirects(submit_new_pass_response, reverse('accounts:password_reset_complete'))

        # 7. Test password reset complete view renders
        complete_response = self.client.get(reverse('accounts:password_reset_complete'))
        self.assertEqual(complete_response.status_code, 200)
        self.assertContains(complete_response, "Password successfully updated")

        # 8. Verify user can log in with new password
        user.refresh_from_db()
        self.assertTrue(user.check_password(new_password))
        login_success = self.client.login(username=user.email, password=new_password)
        self.assertTrue(login_success)


