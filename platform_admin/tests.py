from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
import datetime

from accounts.models import User
from blog.models import Post, PostCategory
from opportunities.models import Opportunity
from assistance.models import AssistanceBooking, AssistancePackage
from subscriptions.models import PaymentTransaction


class PlatformAdminTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            username='student',
            email='student@example.com',
            password='Password123!'
        )

        # Create staff user
        self.staff_user = User.objects.create_user(
            username='admin_user',
            email='admin@flii.io',
            password='Password123!',
            is_staff=True
        )

        # Create category
        self.category = PostCategory.objects.create(
            name='Scholarship Guides',
            slug='scholarship-guides'
        )

        # Create sample opportunity
        self.opp = Opportunity.objects.create(
            title="DAAD Helmut Schmidt Master 2026",
            provider="DAAD",
            country="Germany",
            degree_level="masters",
            funding_type="fully_funded",
            field_of_study="Public Policy",
            description="Policy Master scholarship in Germany",
            funding_details="Full stipend €934/month + tuition + travel",
            eligibility_summary="Open to developing nations with 2:1 degree",
            application_url="https://daad.de/apply",
            official_source_url="https://daad.de/info",
            deadline=timezone.now() + datetime.timedelta(days=60),
            academic_requirement="Bachelor 2:1",
            language_requirement="English B2",
            nationality_requirement="Developing countries",
            documents_required="CV, Statement of Motivation, Transcripts"
        )

        # Create assistance booking
        self.booking = AssistanceBooking.objects.create(
            user=self.regular_user,
            package_title="SOP & Motivation Letter Expert Review",
            service_type="essay_review",
            price=Decimal("15000.00"),
            currency="NGN",
            status="pending_payment",
            payment_status="unpaid",
            contact_email=self.regular_user.email,
            applicant_notes="Need help polishing my motivation letter for Chevening."
        )

    def test_permission_denied_for_regular_user(self):
        self.client.force_login(self.regular_user)
        response = self.client.get(reverse('platform_admin:dashboard'))
        self.assertEqual(response.status_code, 302)
        # Should redirect to student dashboard
        self.assertIn('/dashboard/', response.url)

    def test_staff_access_to_dashboard(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('platform_admin:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Command Center Overview")
        self.assertContains(response, "Assistance Revenue")

    def test_blog_management_flow(self):
        self.client.force_login(self.staff_user)

        # 1. Post new blog article
        create_url = reverse('platform_admin:blog_create')
        post_data = {
            'title': 'How to Win the Erasmus Mundus Joint Masters Scholarship',
            'slug': 'how-to-win-erasmus-mundus',
            'category': self.category.id,
            'summary': 'A strategic step-by-step masterclass on winning EMJM full funding.',
            'content': '## Overview\nErasmus Mundus awards up to €1,400 monthly stipend.',
            'status': 'published',
            'tags': 'Erasmus, Europe, Fully Funded',
            'featured_image_url': 'https://images.unsplash.com/photo-test',
        }
        res_create = self.client.post(create_url, post_data)
        self.assertEqual(res_create.status_code, 302)
        self.assertTrue(Post.objects.filter(slug='how-to-win-erasmus-mundus').exists())

        post = Post.objects.get(slug='how-to-win-erasmus-mundus')
        self.assertEqual(post.author, self.staff_user)
        self.assertEqual(post.status, 'published')

        # 2. Toggle status to draft
        toggle_url = reverse('platform_admin:blog_toggle_status', kwargs={'pk': post.id})
        self.client.post(toggle_url)
        post.refresh_from_db()
        self.assertEqual(post.status, 'draft')

        # 3. Edit article
        edit_url = reverse('platform_admin:blog_edit', kwargs={'pk': post.id})
        post_data['title'] = 'Updated Erasmus Mundus 2026/2027 Guide'
        post_data['status'] = 'published'
        self.client.post(edit_url, post_data)
        post.refresh_from_db()
        self.assertEqual(post.title, 'Updated Erasmus Mundus 2026/2027 Guide')
        self.assertEqual(post.status, 'published')

    def test_blog_wysiwyg_html_and_validation(self):
        self.client.force_login(self.staff_user)
        create_url = reverse('platform_admin:blog_create')

        # 1. Post with WYSIWYG formatted HTML
        wysiwyg_data = {
            'title': 'Mastering Chevening Interviews 2026',
            'slug': 'mastering-chevening-interviews-2026',
            'category': self.category.id,
            'summary': 'In-depth breakdown of leadership and networking interview questions.',
            'content': '<h2>Top Strategy</h2><p>Structure your answers using the <strong>STAR method</strong>.</p><ul><li>Situation</li><li>Task</li></ul>',
            'status': 'published',
            'tags': 'Chevening, Interview, UK',
        }
        response = self.client.post(create_url, wysiwyg_data)
        self.assertEqual(response.status_code, 302)
        post = Post.objects.get(slug='mastering-chevening-interviews-2026')
        self.assertTrue(post.has_html_content)
        self.assertIn('<strong>STAR method</strong>', post.content)

        # 2. Reject empty or WYSIWYG empty paragraph submission
        empty_data = wysiwyg_data.copy()
        empty_data['slug'] = 'empty-article'
        empty_data['content'] = '<p><br></p>'
        response_empty = self.client.post(create_url, empty_data)
        self.assertEqual(response_empty.status_code, 200)
        self.assertContains(response_empty, "Article body content cannot be empty.")
        self.assertFalse(Post.objects.filter(slug='empty-article').exists())

    def test_opportunity_upload_flow(self):
        self.client.force_login(self.staff_user)

        # Upload scholarship manually
        upload_url = reverse('platform_admin:opportunity_create')
        opp_data = {
            'title': 'Commonwealth Shared Scholarships 2026',
            'slug': 'commonwealth-shared-2026',
            'provider': 'Commonwealth Scholarship Commission',
            'university': 'Participating UK Universities',
            'country': 'United Kingdom',
            'degree_level': 'masters',
            'funding_type': 'fully_funded',
            'field_of_study': 'Development Studies & Sustainability',
            'description': 'Prestigious full scholarship for master students from developing nations.',
            'funding_details': 'Full tuition, flight tickets, visa reimbursement, £1,347 monthly living allowance.',
            'eligibility_summary': 'Open to Commonwealth developing countries, minimum 2:1 degree.',
            'opening_date': (timezone.now()).strftime('%Y-%m-%dT%H:%M'),
            'deadline': (timezone.now() + datetime.timedelta(days=90)).strftime('%Y-%m-%dT%H:%M'),
            'deadline_timezone': 'UTC',
            'cycle_name': '2026/2027 Academic Year',
            'start_date': (timezone.now().date() + datetime.timedelta(days=300)).strftime('%Y-%m-%d'),
            'duration': '12 Months (1 Year)',
            'application_url': 'https://cscuk.fcdo.gov.uk/apply',
            'official_source_url': 'https://cscuk.fcdo.gov.uk/scholarships',
            'portal_type': 'direct_portal',
            'academic_requirement': 'Minimum Second Class Upper (2:1)',
            'language_requirement': 'IELTS 6.5 or equivalent',
            'work_experience_requirement': 'None required',
            'nationality_requirement': 'Commonwealth developing countries (Nigeria, Kenya, Ghana)',
            'documents_required': 'Transcripts, References, Essay, Passport',
            'how_to_apply': 'Apply through the online portal before the deadline.',
            'application_fee': 'Free / No Application Fee',
            'status': 'active',
            'verification_status': 'source_verified',
            'image_url': 'https://images.unsplash.com/photo-scholarship'
        }
        res_upload = self.client.post(upload_url, opp_data)
        self.assertEqual(res_upload.status_code, 302)
        self.assertTrue(Opportunity.objects.filter(slug='commonwealth-shared-2026').exists())

        # Toggle featured hero
        created_opp = Opportunity.objects.get(slug='commonwealth-shared-2026')
        self.assertFalse(created_opp.is_featured)
        self.client.post(reverse('platform_admin:opportunity_toggle_featured', kwargs={'pk': created_opp.id}))
        created_opp.refresh_from_db()
        self.assertTrue(created_opp.is_featured)

    def test_registered_users_management(self):
        self.client.force_login(self.staff_user)

        # 1. User list
        res_list = self.client.get(reverse('platform_admin:user_list'))
        self.assertEqual(res_list.status_code, 200)
        self.assertContains(res_list, self.regular_user.email)

        # 2. User 360° inspector
        res_detail = self.client.get(reverse('platform_admin:user_detail', kwargs={'user_id': self.regular_user.id}))
        self.assertEqual(res_detail.status_code, 200)
        self.assertContains(res_detail, self.regular_user.email)

        # 3. Toggle active
        toggle_active_url = reverse('platform_admin:user_toggle_active', kwargs={'user_id': self.regular_user.id})
        self.client.post(toggle_active_url)
        self.regular_user.refresh_from_db()
        self.assertFalse(self.regular_user.is_active)

        # 4. Export CSV
        res_csv = self.client.get(reverse('platform_admin:user_export'))
        self.assertEqual(res_csv.status_code, 200)
        self.assertEqual(res_csv['Content-Type'], 'text/csv')

    def test_paid_requests_management(self):
        self.client.force_login(self.staff_user)

        # 1. Paid requests hub list
        res_hub = self.client.get(reverse('platform_admin:paid_requests'))
        self.assertEqual(res_hub.status_code, 200)
        self.assertContains(res_hub, self.booking.order_number)

        # 2. Inspect order & verify payment status
        detail_url = reverse('platform_admin:paid_request_detail', kwargs={'pk': self.booking.id})
        res_detail = self.client.get(detail_url)
        self.assertEqual(res_detail.status_code, 200)

        # Mark paid
        self.client.post(detail_url, {
            'action': 'update_payment_status',
            'payment_status': 'paid'
        })
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.payment_status, 'paid')
        self.assertEqual(self.booking.status, 'awaiting_assignment')

        # Assign reviewer
        self.client.post(detail_url, {
            'action': 'assign_reviewer',
            'reviewer_id': self.staff_user.id
        })
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.assigned_reviewer, self.staff_user)

        # Submit deliverable & complete
        self.client.post(detail_url, {
            'action': 'submit_deliverable',
            'deliverable_feedback': 'Your essay draft is admissions-ready. Strong STAR alignment in paragraphs 2 and 4.'
        })
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'completed')
        self.assertIsNotNone(self.booking.completed_at)

    def test_category_optional_and_provision_flows(self):
        self.client.force_login(self.staff_user)

        # 1. Post article without category (category is optional)
        create_url = reverse('platform_admin:blog_create')
        post_data = {
            'title': 'General Study Abroad Announcement 2026',
            'slug': 'general-study-abroad-announcement-2026',
            'category': '',  # Empty category
            'summary': 'General information not tied to a specific category.',
            'content': '<p>This is general content without category requirement.</p>',
            'status': 'published',
        }
        res = self.client.post(create_url, post_data)
        self.assertEqual(res.status_code, 302)
        post = Post.objects.get(slug='general-study-abroad-announcement-2026')
        self.assertIsNone(post.category)

        # 2. Quick-create category via AJAX endpoint
        quick_create_url = reverse('platform_admin:blog_category_quick_create')
        res_quick = self.client.post(quick_create_url, {
            'name': 'Work Visas & Permits',
            'badge_color': 'bg-rose-50 text-rose-700 border-rose-200',
            'icon': 'briefcase',
            'description': 'Work permits and post-study work routes.',
        })
        self.assertEqual(res_quick.status_code, 200)
        data = res_quick.json()
        self.assertTrue(data['success'])
        new_cat_id = data['category']['id']
        self.assertTrue(PostCategory.objects.filter(id=new_cat_id).exists())
        new_cat = PostCategory.objects.get(id=new_cat_id)
        self.assertEqual(new_cat.slug, 'work-visas-permits')

        # 3. View category list
        cat_list_url = reverse('platform_admin:blog_category_list')
        res_list = self.client.get(cat_list_url)
        self.assertEqual(res_list.status_code, 200)
        self.assertContains(res_list, 'Work Visas &amp; Permits')
        self.assertContains(res_list, 'work-visas-permits')

        # 4. Create category via standard form in category list
        res_cat_create = self.client.post(cat_list_url, {
            'name': 'Language Tests',
            'badge_color': 'bg-purple-50 text-purple-700 border-purple-200',
            'icon': 'book-open',
            'description': 'IELTS, TOEFL and PTE preparation.',
        })
        self.assertEqual(res_cat_create.status_code, 302)
        self.assertTrue(PostCategory.objects.filter(name='Language Tests').exists())

        # 5. Delete category and ensure linked posts become uncategorized
        post.category = new_cat
        post.save()
        delete_cat_url = reverse('platform_admin:blog_category_delete', kwargs={'pk': new_cat.id})
        res_del = self.client.post(delete_cat_url)
        self.assertEqual(res_del.status_code, 302)
        self.assertFalse(PostCategory.objects.filter(id=new_cat.id).exists())
        post.refresh_from_db()
        self.assertIsNone(post.category)
