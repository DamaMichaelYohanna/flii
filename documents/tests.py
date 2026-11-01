from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from documents.models import Document

User = get_user_model()

class DocumentVaultTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='vaultuser', email='vault@test.com', password='password123')
        self.other_user = User.objects.create_user(username='otheruser', email='other@test.com', password='password123')
        self.client = Client()
        self.client.force_login(self.user)

        # Create a sample document
        sample_pdf = SimpleUploadedFile("transcript.pdf", b"%PDF-1.4 test content", content_type="application/pdf")
        self.doc = Document.objects.create(
            user=self.user,
            title="My University Transcript",
            document_type="transcript",
            file=sample_pdf,
            notes="Official stamped copy"
        )

    def test_document_model_properties(self):
        self.assertEqual(self.doc.file_extension, "pdf")
        self.assertTrue(self.doc.is_previewable)
        self.assertTrue(len(self.doc.formatted_size) > 0)

    def test_document_list_view(self):
        response = self.client.get(reverse('documents:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My University Transcript")
        self.assertContains(response, "openDocumentViewer")
        self.assertContains(response, "documentViewerModal")

    def test_document_view_inline(self):
        response = self.client.get(reverse('documents:view', args=[self.doc.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get('Content-Type'), 'application/pdf')
        # Check inline disposition (not attachment)
        disposition = response.headers.get('Content-Disposition', '')
        self.assertIn('inline', disposition.lower())

    def test_document_download(self):
        response = self.client.get(reverse('documents:download', args=[self.doc.id]))
        self.assertEqual(response.status_code, 200)
        disposition = response.headers.get('Content-Disposition', '')
        self.assertIn('attachment', disposition.lower())

    def test_document_view_user_isolation(self):
        # Other user should not be able to view another user's document
        other_client = Client()
        other_client.force_login(self.other_user)
        response = other_client.get(reverse('documents:view', args=[self.doc.id]))
        self.assertEqual(response.status_code, 404)

    def test_document_delete_user_isolation(self):
        other_client = Client()
        other_client.force_login(self.other_user)
        response = other_client.post(reverse('documents:delete', args=[self.doc.id]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Document.objects.filter(id=self.doc.id).exists())

    def test_document_upload_success(self):
        uploaded = SimpleUploadedFile("cv.pdf", b"%PDF-1.4 sample cv", content_type="application/pdf")
        response = self.client.post(reverse('documents:list'), {
            'title': 'New Academic CV',
            'document_type': 'cv',
            'file': uploaded,
            'notes': 'Updated 2026'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Document.objects.filter(title='New Academic CV').exists())
