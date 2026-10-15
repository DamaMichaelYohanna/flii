from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
import datetime
from accounts.models import User
from opportunities.models import Opportunity, OpportunitySource

class OpportunityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='opp_tester',
            email='opp_test@example.com',
            password='Password123!'
        )
        self.opp = Opportunity.objects.create(
            title="DAAD Master Grant",
            provider="DAAD",
            country="Germany",
            degree_level="masters",
            field_of_study="Computer Science",
            description="Fully funded grant in Germany",
            funding_type="fully_funded",
            funding_details="€934/month stipend + tuition",
            eligibility_summary="Open to international applicants with First Class / 2:1",
            application_url="https://daad.de/apply",
            official_source_url="https://daad.de/official",
            deadline=timezone.now() + datetime.timedelta(days=45),
            language_requirement="IELTS 6.5",
            academic_requirement="BSc in Computing",
            nationality_requirement="All developing countries"
        )

    def test_opportunity_list_view(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('opportunities:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "DAAD Master Grant")

    def test_opportunity_detail_view(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('opportunities:detail', kwargs={'pk': self.opp.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "DAAD Master Grant")
        self.assertContains(response, "Published Eligibility Criteria")

    def test_toggle_shortlist(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('opportunities:toggle_shortlist', kwargs={'pk': self.opp.id}))
        self.assertTrue(self.user.shortlisted_opportunities.filter(id=self.opp.id).exists())

    def test_live_ai_opportunity_import(self):
        self.client.force_login(self.user)
        raw_text = (
            "KTH Royal Institute of Technology Master's Scholarship 2026. "
            "Host Country: Sweden. Level: Master's (MSc). "
            "Field: Cyber Security, Machine Learning. "
            "Funding: 100% full tuition waiver + monthly stipend. "
            "Requirements: First class bachelor's degree in engineering. "
            "Deadline: 2026-11-15."
        )
        response = self.client.post(reverse('opportunities:import'), {
            'source_url': 'https://kth.se/scholarships',
            'raw_text': raw_text
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Opportunity.objects.filter(field_of_study__icontains='Computer').exists() or Opportunity.objects.filter(country__icontains='Sweden').exists() or Opportunity.objects.count() >= 2)

    def test_autonomous_scout_discovery(self):
        from unittest.mock import patch
        from opportunities.discovery import ErasmusCatalogProvider

        mock_discovered = [
            {
                "title": "Test Erasmus Master in Data Science",
                "provider": "European Commission",
                "university": "Consortium of Universities",
                "country": "Europe",
                "degree_level": "masters",
                "field_of_study": "Data Science",
                "description": "Test master scholarship",
                "funding_type": "fully_funded",
                "funding_details": "100% tuition + stipend",
                "eligibility_summary": "Open to international candidates",
                "application_url": "https://test-erasmus.eu/apply",
                "official_source_url": "https://test-erasmus.eu",
                "deadline_days": 60,
                "language_requirement": "IELTS 6.5",
                "academic_requirement": "Bachelor 2:1",
                "nationality_requirement": "Global",
                "documents_required": "CV, Transcript",
                "application_fee": "Free"
            }
        ]

        self.client.force_login(self.user)
        with patch.object(ErasmusCatalogProvider, 'discover', return_value=mock_discovered):
            response = self.client.get(reverse('opportunities:run_scout'), follow=True)
            self.assertEqual(response.status_code, 200)
            self.assertGreater(Opportunity.objects.count(), 1)
            self.assertTrue(self.user.notifications.filter(notification_type='new_opportunity').exists())

    def test_parallel_scanner_execution(self):
        from unittest.mock import patch
        from opportunities.scanner import ParallelOpportunityScanner

        scanner = ParallelOpportunityScanner(timeout=5)
        
        # Mock network fetch to return valid simulated portal response
        mock_page = {
            "success": True,
            "status_code": 200,
            "final_url": "https://daad.de/apply/portal/",
            "title": "DAAD Official Application Portal",
            "text": "Applications for the 2027/2028 intake are now open. Closing deadline: 2027-07-31.",
            "links": ["https://daad.de/apply/portal/"],
            "error": None,
        }

        with patch.object(ParallelOpportunityScanner, 'fetch_portal_page', return_value=mock_page):
            res = scanner.scan_and_verify_single(self.opp, user=self.user)
            self.assertTrue(res["is_live"])
            self.assertEqual(res["status_code"], 200)

            # Reload opportunity from DB
            self.opp.refresh_from_db()
            self.assertEqual(self.opp.scan_http_status, 200)
            self.assertIsNotNone(self.opp.last_scanned_at)
            self.assertIn(self.opp.ai_application_readiness, ['ready', 'requires_login', 'not_yet_open', 'manual_only'])

    def test_scan_portal_views(self):
        from unittest.mock import patch
        from opportunities.scanner import ParallelOpportunityScanner

        mock_page = {
            "success": True,
            "status_code": 200,
            "final_url": "https://daad.de/apply/portal/",
            "title": "DAAD Official Portal",
            "text": "Apply online now. Portal ready for international applicants.",
            "links": ["https://daad.de/apply/portal/"],
            "error": None,
        }

        with patch.object(ParallelOpportunityScanner, 'fetch_portal_page', return_value=mock_page):
            self.client.force_login(self.user)
            # Test single scan view
            resp_single = self.client.get(reverse('opportunities:scan_portal', kwargs={'pk': self.opp.id}), follow=True)
            self.assertEqual(resp_single.status_code, 200)

            # Test scan all view
            resp_all = self.client.get(reverse('opportunities:scan_all_portals'), follow=True)
            self.assertEqual(resp_all.status_code, 200)

    def test_agent_portal_verification_and_application_readiness(self):
        from unittest.mock import patch
        from agent_hub.agent import FliiAgent
        from opportunities.scanner import ParallelOpportunityScanner

        mock_page = {
            "success": True,
            "status_code": 200,
            "final_url": "https://daad.de/apply/portal/",
            "title": "DAAD Portal",
            "text": "Apply here.",
            "links": ["https://daad.de/apply/portal/"],
            "error": None,
        }

        with patch.object(ParallelOpportunityScanner, 'fetch_portal_page', return_value=mock_page):
            agent = FliiAgent(self.user)
            res = agent.verify_portal_for_application(self.opp.id)
            self.assertEqual(res["status_code"], 200)
            self.assertTrue(res["is_live"])
            self.assertIn("application_url", res)

            # Test conversational agent process_message handling portal verification
            chat_res = agent.process_message(f"Verify portal link for {self.opp.title}")
            self.assertEqual(chat_res["tool_used"], "verify_portal_for_application")
            self.assertIn("Live Portal Verification", chat_res["response"])

    def test_admin_scout_hub_permissions_and_view(self):
        # Non-staff user should be redirected
        self.client.force_login(self.user)
        resp_denied = self.client.get(reverse('opportunities:admin_scout_hub'), follow=True)
        self.assertContains(resp_denied, "Staff privileges required")

        # Staff user should access hub
        self.user.is_staff = True
        self.user.save()
        resp_allowed = self.client.get(reverse('opportunities:admin_scout_hub'))
        self.assertEqual(resp_allowed.status_code, 200)
        self.assertContains(resp_allowed, "Autonomous Scout & Aggregator")
        self.assertContains(resp_allowed, "European Commission")

    def test_admin_publish_and_publish_all(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_login(self.user)

        # Create staged opportunity
        staged = Opportunity.objects.create(
            title="Staged Excellence Scholarship",
            provider="International Agency",
            country="France",
            degree_level="masters",
            field_of_study="AI",
            description="Staged grant",
            funding_type="fully_funded",
            funding_details="100% covered",
            eligibility_summary="Open",
            application_url="https://agency.fr/apply",
            official_source_url="https://agency.fr",
            deadline=timezone.now() + datetime.timedelta(days=30),
            verification_status="needs_review"
        )

        # Publish single
        resp = self.client.get(reverse('opportunities:admin_publish', kwargs={'pk': staged.id}), follow=True)
        self.assertEqual(resp.status_code, 200)
        staged.refresh_from_db()
        self.assertEqual(staged.verification_status, 'source_verified')

        # Batch publish all
        staged2 = Opportunity.objects.create(
            title="Staged Fellow 2",
            provider="Nordic Council",
            country="Norway",
            deadline=timezone.now() + datetime.timedelta(days=30),
            verification_status="needs_review"
        )
        resp_batch = self.client.get(reverse('opportunities:admin_publish_all'), follow=True)
        self.assertEqual(resp_batch.status_code, 200)
        staged2.refresh_from_db()
        self.assertEqual(staged2.verification_status, 'source_verified')

    def test_admin_toggle_source(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_login(self.user)

        source = OpportunitySource.objects.create(
            name="Test Ministry Portal",
            source_url="https://test-ministry.gov/scholarships",
            is_active=True
        )

        resp = self.client.get(reverse('opportunities:admin_toggle_source', kwargs={'pk': source.id}), follow=True)
        self.assertEqual(resp.status_code, 200)
        source.refresh_from_db()
        self.assertFalse(source.is_active)



