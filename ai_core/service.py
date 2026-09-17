import logging
import os
from typing import Dict, Any, Optional
from django.conf import settings
from .schemas import EligibilityResult, EssayDraftResult, OpportunityExtractionSchema
from .providers import GeminiProvider, DeterministicSafeProvider, BaseAIProvider
from .knowledge_base import PersonalKnowledgeBase
from agent_hub.models import AIAuditLog

logger = logging.getLogger(__name__)

class AIService:
    _instance = None

    def __init__(self):
        self.gemini_key = getattr(settings, 'GEMINI_API_KEY', '') or os.environ.get('GEMINI_API_KEY', '')
        if self.gemini_key:
            self.primary_provider = GeminiProvider(api_key=self.gemini_key)
        else:
            self.primary_provider = DeterministicSafeProvider()
        self.fallback_provider = DeterministicSafeProvider()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = AIService()
        return cls._instance

    def _log_action(self, user, action_type: str, summary: str, input_ref: str = "", output_summary: str = "", status: str = "success"):
        try:
            if user and user.is_authenticated:
                AIAuditLog.objects.create(
                    user=user,
                    action_type=action_type,
                    provider='gemini-2.5-flash' if self.gemini_key else 'deterministic-rules',
                    summary=summary,
                    input_ref=input_ref,
                    output_summary=output_summary,
                    status=status
                )
        except Exception as e:
            logger.warning(f"Failed to record AI audit log: {e}")

    def assess_eligibility(self, user, opportunity) -> EligibilityResult:
        kb = PersonalKnowledgeBase(user)
        user_context = kb.assemble_context()
        
        system_prompt = (
            "You are the ScholarFlow Eligibility Reasoner. Your job is to strictly compare the applicant's verified facts "
            "against the official published scholarship requirements. DO NOT invent eligibility facts. DO NOT claim admission "
            "is guaranteed. If a requirement is not clearly met or documents are unverified, mark as 'needs_clarification'. "
            "Distinguish between satisfied, needs_clarification, and unmet. Calculate a realistic 'profile_fit_score' from 0-100."
        )

        user_prompt = (
            f"SCHOLARSHIP REQUIREMENTS:\n"
            f"Title: {opportunity.title}\n"
            f"Provider: {opportunity.provider}\n"
            f"Country: {opportunity.country}\n"
            f"Degree Level: {opportunity.get_degree_level_display()}\n"
            f"Field: {opportunity.field_of_study}\n"
            f"Academic Requirement: {opportunity.academic_requirement}\n"
            f"Language Requirement: {opportunity.language_requirement}\n"
            f"Nationality Requirement: {opportunity.nationality_requirement}\n"
            f"Work Experience: {opportunity.work_experience_requirement}\n\n"
            f"APPLICANT VERIFIED FACTS:\n"
            f"{kb.get_summary_text()}\n"
        )

        try:
            result = self.primary_provider.generate_structured(system_prompt, user_prompt, EligibilityResult)
            self._log_action(
                user=user,
                action_type="eligibility_assessment",
                summary=f"Assessed eligibility for {opportunity.title}",
                input_ref=f"Opportunity #{opportunity.id}",
                output_summary=f"Status: {result.eligibility_status}, Fit: {result.profile_fit_score}%",
                status="success"
            )
            return result
        except Exception as e:
            logger.warning(f"Primary provider failed, using deterministic safe fallback: {e}")
            fallback_result = self.fallback_provider.generate_structured(system_prompt, user_prompt, EligibilityResult)
            self._log_action(
                user=user,
                action_type="eligibility_assessment",
                summary=f"Assessed eligibility for {opportunity.title} (Fallback)",
                input_ref=f"Opportunity #{opportunity.id}",
                output_summary=f"Status: {fallback_result.eligibility_status}, Fit: {fallback_result.profile_fit_score}%",
                status="warning"
            )
            return fallback_result

    def draft_essay_response(self, user, opportunity, question_title: str, prompt_context: str = "", tone: str = "formal") -> EssayDraftResult:
        kb = PersonalKnowledgeBase(user)
        
        system_prompt = (
            "You are the ScholarFlow AI Writing Assistant. Your mandate is to draft application essays GROUNDED EXCLUSIVELY "
            "in the applicant's verified personal profile, educations, employments, and STAR stories. "
            "RULE 1: NEVER invent jobs, awards, GPAs, percentages, companies, or experiences that do not exist in the applicant context. "
            "RULE 2: If key information is missing, explicitly note: 'I need additional information from you.' "
            "RULE 3: Return structured JSON matching EssayDraftResult."
        )

        user_prompt = (
            f"TARGET OPPORTUNITY:\n"
            f"Title: {opportunity.title} ({opportunity.provider})\n"
            f"Field: {opportunity.field_of_study}\n"
            f"Country: {opportunity.country}\n\n"
            f"APPLICATION ESSAY PROMPT / QUESTION:\n"
            f"{question_title}\n"
            f"Additional Context/Instructions: {prompt_context}\n"
            f"Desired Tone: {tone}\n\n"
            f"APPLICANT KNOWLEDGE BASE (VERIFIED FACTS):\n"
            f"{kb.assemble_context()}\n"
        )

        try:
            result = self.primary_provider.generate_structured(system_prompt, user_prompt, EssayDraftResult)
            self._log_action(
                user=user,
                action_type="essay_drafting",
                summary=f"Drafted essay response for '{question_title}'",
                input_ref=f"Opportunity #{opportunity.id}",
                output_summary=f"Words: {result.word_count}, Stories used: {len(result.used_stories)}",
                status="success"
            )
            return result
        except Exception as e:
            logger.warning(f"Primary provider failed in essay drafting, using fallback: {e}")
            fallback_result = self.fallback_provider.generate_structured(system_prompt, user_prompt, EssayDraftResult)
            self._log_action(
                user=user,
                action_type="essay_drafting",
                summary=f"Drafted essay for '{question_title}' (Fallback)",
                input_ref=f"Opportunity #{opportunity.id}",
                output_summary=f"Words: {fallback_result.word_count}",
                status="warning"
            )
            return fallback_result

    def extract_opportunity_from_text(self, user, raw_text: str, source_url: str = "") -> OpportunityExtractionSchema:
        system_prompt = (
            "You are the ScholarFlow Opportunity Intelligence Extractor. "
            "Extract structured scholarship metadata from the provided official announcement text. "
            "Never invent criteria. Extract exact degree levels, deadline dates, funding specifics, and published requirements. "
            "Return valid JSON matching OpportunityExtractionSchema."
        )

        user_prompt = f"OFFICIAL SOURCE URL: {source_url}\n\nDOCUMENTATION TEXT:\n{raw_text[:4000]}"

        try:
            result = self.primary_provider.generate_structured(system_prompt, user_prompt, OpportunityExtractionSchema)
            if source_url and not result.official_source_url:
                result.official_source_url = source_url
            self._log_action(
                user=user,
                action_type="opportunity_extraction",
                summary=f"Extracted opportunity: {result.title}",
                input_ref=source_url or "Pasted Text",
                output_summary=f"{result.provider} ({result.country}) - Deadline: {result.deadline_iso}",
                status="success"
            )
            return result
        except Exception as e:
            logger.warning(f"Primary provider failed in extraction, using fallback: {e}")
            fallback_result = self.fallback_provider.generate_structured(system_prompt, user_prompt, OpportunityExtractionSchema)
            if source_url and not fallback_result.official_source_url:
                fallback_result.official_source_url = source_url
            self._log_action(
                user=user,
                action_type="opportunity_extraction",
                summary=f"Extracted opportunity: {fallback_result.title} (Fallback)",
                input_ref=source_url or "Pasted Text",
                output_summary=f"{fallback_result.provider} - Deadline: {fallback_result.deadline_iso}",
                status="warning"
            )
            return fallback_result

