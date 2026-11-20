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

    def test_google_login_unconfigured_redirects_to_login(self):
        response = self.client.get(reverse('accounts:google_login'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accounts:login'))

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

    def test_onboarding_express_two_step_flow(self):
        user = User.objects.create_user(
            username='express_scholar',
            email='express@example.com',
            password='Password123!',
            first_name='Chioma'
        )
        self.client.login(username='express@example.com', password='Password123!')

        # 1. Access Step 1
        res = self.client.get(reverse('accounts:onboarding'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Where do you want to study next?")
        self.assertContains(res, "Skip to Dashboard")

        # 2. Submit Step 1: Study Ambitions
        post_step1 = self.client.post(reverse('accounts:onboarding'), {
            'step': 1,
            'target_degree': "Master's (MSc)",
            'target_fields': 'Artificial Intelligence, Data Science',
            'target_countries': 'Germany, United Kingdom',
            'funding_preference': 'fully_funded',
            'career_goals': 'Lead AI research for African languages'
        })
        self.assertRedirects(post_step1, '/onboarding/?step=2')

        # Verify StudyGoal was persisted
        user.refresh_from_db()
        profile = user.applicant_profile
        self.assertTrue(hasattr(profile, 'study_goal'))
        self.assertEqual(profile.study_goal.target_degree, "Master's (MSc)")
        self.assertIn('Germany', profile.study_goal.target_countries)

        # 3. Access Step 2
        res_step2 = self.client.get(reverse('accounts:onboarding') + '?step=2')
        self.assertEqual(res_step2.status_code, 200)
        self.assertContains(res_step2, "Academic Background")

        # 4. Submit Step 2: Academic Snapshot
        post_step2 = self.client.post(reverse('accounts:onboarding'), {
            'step': 2,
            'institution': 'University of Lagos',
            'field_of_study': 'Computer Science',
            'degree_level': 'bachelors',
            'grade_classification': 'First Class Honours',
            'cgpa': '4.85',
            'max_cgpa': '5.00',
            'country_of_origin': 'Nigeria',
            'nationality': 'Nigerian',
            'current_location': 'Lagos, Nigeria',
            'phone': '+2348012345678',
            'headline': 'First-Class CS Graduate | AI Enthusiast'
        })
        self.assertRedirects(post_step2, reverse('dashboard:index'))

        # Verify user marked onboarding complete
        user.refresh_from_db()
        self.assertTrue(user.onboarding_completed)
        self.assertEqual(profile.educations.count(), 1)
        edu = profile.educations.first()
        self.assertEqual(edu.institution, 'University of Lagos')
        self.assertEqual(edu.grade_classification, 'First Class Honours')

    def test_onboarding_skip_link_immediately_unlocks_dashboard(self):
        user = User.objects.create_user(
            username='skipper',
            email='skipper@example.com',
            password='Password123!'
        )
        self.assertFalse(user.onboarding_completed)
        self.client.login(username='skipper@example.com', password='Password123!')

        # Hit skip via GET ?skip=true
        res = self.client.get(reverse('accounts:onboarding') + '?skip=true')
        self.assertRedirects(res, reverse('dashboard:index'))

        user.refresh_from_db()
        self.assertTrue(user.onboarding_completed)

    def test_registration_sends_confirmation_email_and_verification_flow(self):
        from django.core import mail
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        from django.contrib.auth.tokens import default_token_generator

        mail.outbox.clear()

        # 1. Register a new user
        reg_response = self.client.post(reverse('accounts:register'), {
            'username': 'confirmeduser',
            'first_name': 'Chinedu',
            'last_name': 'Okafor',
            'email': 'chinedu@example.com',
            'password1': 'SecurePassword123!',
            'password2': 'SecurePassword123!',
        })
        self.assertRedirects(reg_response, reverse('accounts:onboarding'))

        # User is created but unverified initially
        user = User.objects.get(email='chinedu@example.com')
        self.assertFalse(user.is_email_verified)

        # 2. Check outbox for verification email
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.to, ['chinedu@example.com'])
        self.assertIn("Confirm your email address", msg.subject)
        self.assertIn("verify-email", msg.body)
        self.assertTrue(any(content_type == 'text/html' for _, content_type in msg.alternatives))

        # 3. Simulate clicking valid verification link
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        verify_url = reverse('accounts:verify_email', kwargs={'uidb64': uidb64, 'token': token})

        verify_response = self.client.get(verify_url)
        # Authenticated user gets redirected forward to onboarding
        self.assertRedirects(verify_response, reverse('accounts:onboarding'))

        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)

    def test_verify_email_invalid_token(self):
        user = User.objects.create_user(
            username='invalidtokenuser',
            email='invalid@example.com',
            password='Password123!'
        )
        self.assertFalse(user.is_email_verified)

        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        # Access with garbage token
        verify_url = reverse('accounts:verify_email', kwargs={'uidb64': uidb64, 'token': 'bad-token-123'})
        response = self.client.get(verify_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Verification Link Expired")

        user.refresh_from_db()
        self.assertFalse(user.is_email_verified)

    def test_resend_verification_email(self):
        from django.core import mail
        mail.outbox.clear()

        user = User.objects.create_user(
            username='resenduser',
            email='resend@example.com',
            password='Password123!'
        )
        self.assertFalse(user.is_email_verified)
        self.client.login(username='resend@example.com', password='Password123!')

        # Resend as authenticated user
        self.client.post(reverse('accounts:resend_verification'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['resend@example.com'])




