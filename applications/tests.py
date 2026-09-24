from django.test import TestCase
from django.utils import timezone
import datetime
from accounts.models import User
from opportunities.models import Opportunity
from applications.models import Application, ApplicationRequirement
from agent_hub.agent import FliiAgent

class ApplicationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='app_user',
            email='app@example.com',
            password='Password123!'
        )
        self.opp = Opportunity.objects.create(
            title="DAAD Helmut Schmidt",
            provider="DAAD",
            country="Germany",
            degree_level="masters",
            field_of_study="Public Policy",
            description="Policy master in Germany",
            funding_type="fully_funded",
            funding_details="Stipend + travel",
            eligibility_summary="Open to developing nations",
            application_url="https://example.com/apply",
            official_source_url="https://example.com/official",
            deadline=timezone.now() + datetime.timedelta(days=40),
            academic_requirement="Bachelor degree 2:1",
            language_requirement="English B2",
            nationality_requirement="DAC countries"
        )

    def test_create_application_via_agent(self):
        agent = FliiAgent(self.user)
        result = agent.create_application(self.opp.id)
        self.assertTrue(result['created'])
        app = Application.objects.get(id=result['application_id'])
        self.assertEqual(app.requirements.count(), 7)

    def test_autonomous_assembler(self):
        from applicants.models import ApplicantProfile, Education
        from documents.models import Document
        from applications.services import AutonomousApplicationAssembler

        # Setup profile
        profile = ApplicantProfile.objects.create(
            user=self.user,
            nationality="Nigerian",
            country_of_origin="Nigeria",
            headline="CS Graduate"
        )
        Education.objects.create(
            profile=profile,
            institution="University of Lagos",
            field_of_study="Computer Science",
            graduation_year=2024,
            grade_classification="First Class Honours",
            cgpa=4.85
        )

        agent = FliiAgent(self.user)
        res = agent.create_application(self.opp.id)
        app = Application.objects.get(id=res['application_id'])

        # Create user document after application creation
        doc = Document.objects.create(
            user=self.user,
            title="My Academic CV",
            document_type="cv",
            verification_status="verified"
        )

        assembler = AutonomousApplicationAssembler(app, self.user)
        assemble_res = assembler.assemble()

        self.assertTrue(assemble_res['success'])
        self.assertGreaterEqual(assemble_res['attached_docs_count'], 1)
        self.assertGreaterEqual(assemble_res['drafted_essays_count'], 1)

        # Test dossier view
        self.client.force_login(self.user)
        response = self.client.get(f"/applications/{app.id}/dossier/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Application Dossier & Fast-Copy Hub")
        self.assertContains(response, "University of Lagos")



