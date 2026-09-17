import logging
from typing import Dict, Any, List, Optional
from django.utils import timezone
from .models import Application, ApplicationRequirement, ApplicationTask
from documents.models import Document
from ai_core.service import AIService
from agent_hub.models import AIAuditLog, AgentAction
from notifications.models import Notification

logger = logging.getLogger(__name__)

class AutonomousApplicationAssembler:
    """
    Orchestrates one-click autonomous assembly of scholarship application packages.
    Auto-attaches verified vault documents, generates STAR-grounded essay drafts,
    builds the fast-copy dossier, and queues human-in-the-loop review.
    """

    DOC_TYPE_KEYWORDS = {
        'cv': ['cv', 'resume', 'curriculum vitae'],
        'transcript': ['transcript', 'academic record', 'grades', 'mark sheet'],
        'degree_certificate': ['degree certificate', 'statement of result', 'diploma certificate', 'graduation certificate'],
        'passport': ['passport', 'data page', 'travel document', 'identification', 'national id'],
        'english_test': ['english', 'ielts', 'toefl', 'proficiency', 'medium of instruction'],
        'recommendation_letter': ['recommendation', 'reference letter', 'referee'],
        'portfolio': ['portfolio', 'writing sample', 'project report', 'research proposal'],
    }

    ESSAY_KEYWORDS = ['letter', 'statement', 'essay', 'motivation', 'purpose', 'plan', 'proposal', 'question', 'narrative', 'why']

    def __init__(self, application: Application, user):
        self.application = application
        self.user = user
        self.opportunity = application.opportunity
        self.ai_service = AIService.get_instance()

    def assemble(self) -> Dict[str, Any]:
        """
        Executes end-to-end package assembly.
        """
        attached_docs_count = self._auto_attach_documents()
        drafted_essays_count = self._auto_draft_essays()
        tasks_created = self._ensure_submission_tasks()

        # Update application status if it was planning
        if self.application.status == 'planning':
            self.application.status = 'ready_for_review'
            self.application.save()

        # Audit log
        try:
            AIAuditLog.objects.create(
                user=self.user,
                action_type="autonomous_dossier_assembly",
                provider="scholarflow_autonomous_pipeline",
                summary=f"Assembled full application package for {self.opportunity.title}: {attached_docs_count} docs linked, {drafted_essays_count} essays drafted.",
                input_ref=f"Application #{self.application.id}",
                output_summary=f"Readiness: {self.application.progress_percentage}%. Tasks generated: {tasks_created}.",
                status="success"
            )
        except Exception as e:
            logger.warning(f"Failed to record AIAuditLog: {e}")

        # In-app notification
        try:
            Notification.objects.create(
                user=self.user,
                notification_type='application_milestone',
                title=f"Package Assembled: {self.opportunity.title}",
                message=f"Your complete application dossier with {drafted_essays_count} drafted essays and {attached_docs_count} linked documents is ready for fast portal submission.",
                action_url=f"/applications/{self.application.id}/"
            )
        except Exception as e:
            logger.warning(f"Failed to create notification: {e}")

        return {
            "success": True,
            "attached_docs_count": attached_docs_count,
            "drafted_essays_count": drafted_essays_count,
            "tasks_created": tasks_created,
            "progress_percentage": self.application.progress_percentage
        }

    def _auto_attach_documents(self) -> int:
        count = 0
        user_docs = list(self.user.documents.all())
        requirements = self.application.requirements.filter(attached_document__isnull=True)

        for req in requirements:
            req_name_lower = req.name.lower() + " " + req.description.lower()
            matched_doc = None

            for doc_type, keywords in self.DOC_TYPE_KEYWORDS.items():
                if any(kw in req_name_lower for kw in keywords):
                    # Find matching document in user vault
                    candidates = [d for d in user_docs if d.document_type == doc_type]
                    if candidates:
                        # Prioritize verified documents
                        verified_candidates = [d for d in candidates if d.verification_status == 'verified']
                        matched_doc = verified_candidates[0] if verified_candidates else candidates[0]
                        break

            if matched_doc:
                req.attached_document = matched_doc
                req.status = 'complete'
                req.save()
                count += 1

        return count

    def _auto_draft_essays(self) -> int:
        count = 0
        # Strictly target requirements that are designated as essays
        for req in self.application.requirements.all():
            if req.requirement_type == 'document':
                # Clear any accidental draft responses on document uploads
                if req.draft_response:
                    req.draft_response = ""
                    req.ai_grounding_notes = ""
                    if not req.attached_document:
                        req.status = 'not_started'
                    req.save()
                continue

            # This is an essay requirement
            try:
                draft_result = self.ai_service.draft_essay_response(
                    user=self.user,
                    opportunity=self.opportunity,
                    question_title=req.name,
                    prompt_context=req.description,
                    tone="academic_formal"
                )
                req.draft_response = draft_result.draft_content
                req.ai_grounding_notes = (
                    f"Grounded in {len(draft_result.used_stories)} STAR stories and "
                    f"{len(draft_result.used_facts)} profile facts. "
                    f"Word count: {draft_result.word_count}."
                )
                req.status = 'needs_review'
                req.save()
                count += 1
            except Exception as e:
                logger.error(f"Error drafting essay for {req.name}: {e}")

        return count


    def _ensure_submission_tasks(self) -> int:
        standard_tasks = [
            ("Proofread AI-drafted essays & tailor final closing lines", "Review generated Statement of Purpose / Motivation Letter in the Dossier hub."),
            ("Confirm referee email addresses & notify recommenders", "Ensure your academic referees know about this application deadline."),
            ("Complete official portal submission & paste confirmation ID", "Copy fields from ScholarFlow Dossier into the official university portal.")
        ]
        created_count = 0
        existing_titles = set(self.application.tasks.values_list('title', flat=True))

        for title, desc in standard_tasks:
            if title not in existing_titles:
                ApplicationTask.objects.create(
                    application=self.application,
                    title=title,
                    description=desc,
                    created_by_ai=True,
                    due_date=self.opportunity.deadline
                )
                created_count += 1

        return created_count

    def build_dossier_data(self) -> Dict[str, Any]:
        """
        Compiles the complete field-by-field Application Dossier for quick copying.
        """
        profile = getattr(self.user, 'applicant_profile', None)
        educations = list(profile.educations.all()) if profile else []
        employments = list(profile.employments.all()) if profile else []
        skills = list(profile.skills.all()) if profile else []
        stories = list(self.user.stories.all())
        requirements = list(self.application.requirements.all())

        # Top education
        primary_edu = educations[0] if educations else None

        dossier = {
            "application_id": self.application.id,
            "opportunity_title": self.opportunity.title,
            "provider": self.opportunity.provider,
            "country": self.opportunity.country,
            "deadline": self.opportunity.deadline,
            "application_url": self.opportunity.application_url,
            "progress_percentage": self.application.progress_percentage,
            
            # Fast Copy: Personal Info
            "personal_info": {
                "full_name": profile.full_name if profile else self.user.get_full_name(),
                "first_name": self.user.first_name,
                "middle_name": profile.middle_name if profile else "",
                "last_name": self.user.last_name,
                "email": self.user.email,
                "phone": profile.phone if profile else "",
                "nationality": profile.nationality if profile else "Nigerian",
                "country_of_origin": profile.country_of_origin if profile else "Nigeria",
                "date_of_birth": profile.date_of_birth.strftime('%Y-%m-%d') if (profile and profile.date_of_birth) else "",
                "current_location": profile.current_location if profile else "",
                "headline": profile.headline if profile else "",
                "bio_summary": profile.bio_summary if profile else "",
            },

            # Fast Copy: Academic Records
            "primary_education": {
                "institution": primary_edu.institution if primary_edu else "",
                "degree_level": primary_edu.get_degree_level_display() if primary_edu else "",
                "field_of_study": primary_edu.field_of_study if primary_edu else "",
                "graduation_year": primary_edu.graduation_year if primary_edu else "",
                "grade_classification": primary_edu.grade_classification if primary_edu else "",
                "cgpa": f"{primary_edu.cgpa} / {primary_edu.max_cgpa}" if (primary_edu and primary_edu.cgpa) else "",
            },
            "all_educations": educations,
            "all_employments": employments,
            "top_skills": [s.name for s in skills[:10]],

            # Fast Copy: Application Documents & Drafted Essays
            "requirements": requirements,
            "essay_requirements": [r for r in requirements if r.draft_response],
            "document_requirements": [r for r in requirements if r.attached_document],
        }

        return dossier
