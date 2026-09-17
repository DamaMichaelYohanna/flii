from django.test import TestCase
from django.utils import timezone
import datetime
from accounts.models import User
from applicants.models import ApplicantProfile, Education, StudyGoal
from opportunities.models import Opportunity
from matching.engine import MatchingEngine

class MatchingEngineTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='matching_user',
            email='match@example.com',
            password='Password123!',
            first_name='Match',
            last_name='User'
        )
        self.profile = ApplicantProfile.objects.create(
            user=self.user,
            country_of_origin='Nigeria',
            nationality='Nigerian'
        )
        Education.objects.create(
            profile=self.profile,
            institution='University of Lagos',
            degree_level='bachelors',
            field_of_study='Computer Science',
            grade_classification='First Class Honours',
            cgpa=4.80,
            max_cgpa=5.00
        )
        StudyGoal.objects.create(
            profile=self.profile,
            target_degree="Master's (MSc)",
            target_fields="Artificial Intelligence, Computer Science",
            target_countries="Germany, Europe",
            funding_preference="fully_funded"
        )
        self.opp = Opportunity.objects.create(
            title="Erasmus AI Master",
            provider="EU",
            country="European Union",
            degree_level="masters",
            field_of_study="Artificial Intelligence",
            description="Prestigious joint master",
            funding_type="fully_funded",
            funding_details="Full stipend + tuition",
            eligibility_summary="Open to all STEM graduates with First Class or 2:1",
            application_url="https://example.com/apply",
            official_source_url="https://example.com/official",
            deadline=timezone.now() + datetime.timedelta(days=60),
            academic_requirement="First Class in Computing",
            language_requirement="IELTS 6.5",
            nationality_requirement="Open to all (Nigeria included)"
        )

    def test_deterministic_fit_calculation(self):
        engine = MatchingEngine(self.user)
        fit = engine.calculate_deterministic_fit(self.opp)
        self.assertGreaterEqual(fit['score'], 75)
        self.assertEqual(fit['status'], 'likely_eligible')

    def test_ai_eligibility_assessment(self):
        engine = MatchingEngine(self.user)
        result = engine.assess_full_eligibility(self.opp)
        self.assertIn(result.eligibility_status, ['likely_eligible', 'confirmed_eligible'])
        self.assertGreater(len(result.matched_requirements), 0)
