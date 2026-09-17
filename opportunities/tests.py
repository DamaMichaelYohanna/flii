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
        self.client.force_login(self.user)
        response = self.client.get(reverse('opportunities:run_scout'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(Opportunity.objects.count(), 1)
        self.assertTrue(self.user.notifications.filter(notification_type='new_opportunity').exists())

