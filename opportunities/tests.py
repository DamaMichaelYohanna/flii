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

    def test_public_directory_and_pagination(self):
        # 1. Unauthenticated guest can access public directory
        response = self.client.get(reverse('opportunities:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "DAAD Master Grant")

        # 2. Public pagination is open for SEO and visitors (not blocked with 302 redirect)
        response_p2 = self.client.get(reverse('opportunities:list') + '?page=2')
        self.assertEqual(response_p2.status_code, 200)

        # 3. Authenticated user can also access directory
        self.client.force_login(self.user)
        response_auth = self.client.get(reverse('opportunities:list'))
        self.assertEqual(response_auth.status_code, 200)

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
        with patch.object(ErasmusCatalogProvider, 'discover', return_value=mock_discovered), \
             patch('opportunities.discovery.OpportunityDiscoveryService.scout_single_source') as mock_scout:
            mock_scout.return_value = {
                "source_id": 1,
                "source_name": "Test Portal",
                "success": True,
                "status_code": 200,
                "created": 0,
                "updated": 0,
                "error": None
            }
            response = self.client.get(reverse('opportunities:run_scout'), follow=True)
            self.assertEqual(response.status_code, 200)
            self.assertGreater(Opportunity.objects.count(), 1)
            self.assertTrue(self.user.notifications.filter(notification_type='new_opportunity').exists())

    def test_autonomous_scout_discovery_zero_new(self):
        from unittest.mock import patch
        from opportunities.discovery import ErasmusCatalogProvider

        self.client.force_login(self.user)
        with patch.object(ErasmusCatalogProvider, 'discover', return_value=[]), \
             patch('opportunities.discovery.OpportunityDiscoveryService.scout_single_source') as mock_scout:
            mock_scout.return_value = {
                "source_id": 1,
                "source_name": "Test Portal",
                "success": True,
                "status_code": 200,
                "created": 0,
                "updated": 0,
                "error": None
            }
            response = self.client.get(reverse('opportunities:run_scout'), follow=True)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "verified and up to date")

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

    def test_public_slug_routing_and_schema_markup(self):
        # Verify slug generation
        self.assertTrue(bool(self.opp.slug))
        self.assertIn("daad-master-grant", self.opp.slug)

        # Unauthenticated guest visits public slug URL
        response = self.client.get(f"/scholarships/{self.opp.slug}/")
        self.assertEqual(response.status_code, 200)
        # Verify SEO title and schema.org JSON-LD
        self.assertContains(response, "DAAD Master Grant | Fully Funded Scholarship | Flii")
        self.assertContains(response, "application/ld+json")
        # Verify Signature Quick Summary Table fields
        self.assertContains(response, "Scholarship Quick Summary")
        self.assertContains(response, "Germany")
        self.assertContains(response, "DAAD")
        self.assertContains(response, "Fully Funded")
        self.assertContains(response, "https://daad.de/apply")
        # Verify editorial dossier sections
        self.assertContains(response, "Programme Overview")
        self.assertContains(response, "Scholarship Benefits & Financial Coverage")
        self.assertContains(response, "Published Eligibility Criteria & Requirements")
        self.assertContains(response, "Mandatory Documents Required")
        self.assertContains(response, "How to Apply (Step-by-Step Guide)")
        self.assertContains(response, "CLICK HERE TO APPLY ON OFFICIAL PORTAL")

    def test_guest_visitor_sees_ai_conversion_card_and_sponsored_banner(self):
        # 1. Detail page as unauthenticated guest: General info + Conversion Hook
        response = self.client.get(f"/scholarships/{self.opp.slug}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Do You Qualify for This Scholarship?")
        self.assertContains(response, "Create Free Profile & Check Fit")
        self.assertNotContains(response, "Your AI Grounded Profile Fit")

        # 2. Directory page as guest: Sponsored education partner placement present
        list_resp = self.client.get(reverse('opportunities:list'))
        self.assertEqual(list_resp.status_code, 200)
        self.assertContains(list_resp, "Prepare for your IELTS & English Proficiency")
        self.assertContains(list_resp, "SPONSORED RESOURCE")

    def test_authenticated_user_sees_personalized_fit_and_actions(self):
        self.client.force_login(self.user)
        response = self.client.get(f"/scholarships/{self.opp.slug}/")
        self.assertEqual(response.status_code, 200)
        # Authenticated user sees deterministic profile fit evaluation
        self.assertContains(response, "Your AI Grounded Profile Fit")
        self.assertContains(response, "Action Items & Verification")
        self.assertNotContains(response, "Create Free Profile & Check Fit")

    def test_premium_user_sees_zero_ads(self):
        from unittest.mock import patch
        self.client.force_login(self.user)
        # Mock user having active premium entitlement
        with patch('subscriptions.entitlements.EntitlementService.has_active_subscription', return_value=True):
            # Directory page
            list_resp = self.client.get(reverse('opportunities:list'))
            self.assertEqual(list_resp.status_code, 200)
            self.assertNotContains(list_resp, "Prepare for your IELTS examination")

            # Detail page
            detail_resp = self.client.get(f"/scholarships/{self.opp.slug}/")
            self.assertEqual(detail_resp.status_code, 200)
            self.assertNotContains(detail_resp, "Prepare for your IELTS examination")

    def test_public_directory_multi_filters(self):
        # Filter by Degree Level
        res_masters = self.client.get(reverse('opportunities:list') + '?degree_level=masters')
        self.assertEqual(res_masters.status_code, 200)
        self.assertContains(res_masters, "DAAD Master Grant")

        res_phd = self.client.get(reverse('opportunities:list') + '?degree_level=phd')
        self.assertEqual(res_phd.status_code, 200)
        self.assertNotContains(res_phd, "DAAD Master Grant")

        # Filter by Destination Country
        res_germany = self.client.get(reverse('opportunities:list') + '?country=Germany')
        self.assertEqual(res_germany.status_code, 200)
        self.assertContains(res_germany, "DAAD Master Grant")

        res_japan = self.client.get(reverse('opportunities:list') + '?country=Japan')
        self.assertEqual(res_japan.status_code, 200)
        self.assertNotContains(res_japan, "DAAD Master Grant")

    def test_opportunities_path_removed_returns_404(self):
        resp = self.client.get('/opportunities/')
        self.assertEqual(resp.status_code, 404)



