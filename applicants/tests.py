from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import User
from applicants.models import ApplicantProfile, Education, StudyGoal

class ApplicantProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='profile_test_user',
            email='profile_test@example.com',
            password='Password123!'
        )
        self.profile = ApplicantProfile.objects.create(
            user=self.user,
            country_of_origin='Nigeria',
            nationality='Nigerian'
        )

    def test_profile_view_renders_for_authenticated_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('applicants:profile_view'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Structured Applicant Profile")
        self.assertContains(response, "Document Vault")

    def test_document_upload_via_profile(self):
        self.client.force_login(self.user)
        dummy_file = SimpleUploadedFile("my_cv.pdf", b"Dummy CV Content", content_type="application/pdf")
        response = self.client.post(reverse('applicants:profile_view'), {
            'action': 'upload_document',
            'title': 'Test CV Upload',
            'document_type': 'cv',
            'file': dummy_file
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.user.documents.count(), 1)
        self.assertEqual(self.user.documents.first().title, 'Test CV Upload')
