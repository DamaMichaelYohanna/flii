import logging
from typing import Dict, Any, List, Optional
from django.utils import timezone
from opportunities.models import Opportunity
from applications.models import Application, ApplicationRequirement, ApplicationTask
from documents.models import Document
from applicants.models import ApplicantProfile
from ai_core.service import AIService
from ai_core.knowledge_base import PersonalKnowledgeBase
from .models import AgentAction, AIAuditLog
from notifications.models import Notification

logger = logging.getLogger(__name__)

class FliiAgent:
    """
    Modular AI Agent with specialized tool execution and strict human-in-the-loop controls.
    """
    def __init__(self, user):
        self.user = user
        self.ai_service = AIService.get_instance()
        self.kb = PersonalKnowledgeBase(user)

    # ---------------- Tool Registry ----------------
    def get_applicant_profile(self) -> Dict[str, Any]:
        return self.kb.assemble_context()

    def search_opportunities(self, query: str = "", country: str = "", field: str = "", funding_type: str = "") -> List[Dict[str, Any]]:
        qs = Opportunity.objects.filter(status='active')
        if query:
            qs = qs.filter(title__icontains=query) | qs.filter(description__icontains=query) | qs.filter(field_of_study__icontains=query)
        if country:
            qs = qs.filter(country__icontains=country)
        if field:
            qs = qs.filter(field_of_study__icontains=field)
        if funding_type:
            qs = qs.filter(funding_type=funding_type)
        
        results = []
        for opp in qs[:8]:
            results.append({
                "id": opp.id,
                "title": opp.title,
                "provider": opp.provider,
                "country": opp.country,
                "funding_type": opp.get_funding_type_display(),
                "deadline": opp.deadline.strftime("%Y-%m-%d"),
                "days_remaining": opp.days_remaining,
                "application_url": opp.application_url or opp.official_source_url,
                "portal_type": opp.get_portal_type_display(),
                "ai_readiness": opp.get_ai_application_readiness_display(),
                "cycle_badge": opp.cycle_badge,
                "official_source": opp.official_source_url
            })
        return results

    def get_opportunity(self, opportunity_id: int) -> Optional[Dict[str, Any]]:
        try:
            opp = Opportunity.objects.get(id=opportunity_id)
            return {
                "id": opp.id,
                "title": opp.title,
                "provider": opp.provider,
                "country": opp.country,
                "degree_level": opp.get_degree_level_display(),
                "field_of_study": opp.field_of_study,
                "funding_details": opp.funding_details,
                "eligibility_summary": opp.eligibility_summary,
                "application_url": opp.application_url or opp.official_source_url,
                "portal_type": opp.get_portal_type_display(),
                "ai_readiness": opp.get_ai_application_readiness_display(),
                "cycle_name": opp.cycle_name,
                "opening_date": opp.opening_date.strftime("%Y-%m-%d") if opp.opening_date else None,
                "deadline": opp.deadline.strftime("%Y-%m-%d"),
                "academic_requirement": opp.academic_requirement,
                "language_requirement": opp.language_requirement,
                "nationality_requirement": opp.nationality_requirement,
                "documents_required": opp.documents_required,
                "official_source": opp.official_source_url
            }
        except Opportunity.DoesNotExist:
            return None

    def assess_eligibility(self, opportunity_id: int) -> Dict[str, Any]:
        opp = Opportunity.objects.get(id=opportunity_id)
        result = self.ai_service.assess_eligibility(self.user, opp)
        return result.model_dump()

    def verify_portal_for_application(self, opportunity_id: int) -> Dict[str, Any]:
        """
        Launches live parallel AI verification on target scholarship portal.
        Validates URL accessibility and prepares application bundle for AI agent execution.
        """
        from opportunities.scanner import ParallelOpportunityScanner
        opp = Opportunity.objects.get(id=opportunity_id)
        scanner = ParallelOpportunityScanner(timeout=8)
        scan_result = scanner.scan_and_verify_single(opp, user=self.user)
        
        user_docs = set(self.user.documents.values_list('document_type', flat=True))
        has_cv = 'cv' in user_docs
        has_transcript = 'transcript' in user_docs

        return {
            "opportunity_id": opp.id,
            "title": opp.title,
            "application_url": opp.application_url or opp.official_source_url,
            "is_live": scan_result["is_live"],
            "status_code": scan_result["status_code"],
            "portal_type": opp.get_portal_type_display(),
            "ai_readiness": opp.get_ai_application_readiness_display(),
            "cycle_badge": opp.cycle_badge,
            "can_auto_prepare": has_cv and has_transcript,
            "summary": scan_result["summary"]
        }


    def list_missing_documents(self, application_id: Optional[int] = None) -> List[Dict[str, Any]]:
        user_docs = set(self.user.documents.values_list('document_type', flat=True))
        core_types = [
            ('cv', 'Curriculum Vitae (CV) / Resume'),
            ('transcript', 'Official Academic Transcript'),
            ('degree_certificate', 'Degree Certificate / Statement of Result'),
            ('passport', 'International Passport Data Page'),
            ('recommendation_letter', 'Academic Letter of Recommendation'),
            ('english_test', 'English Proficiency / Medium of Instruction Letter')
        ]
        missing = []
        for dtype, label in core_types:
            if dtype not in user_docs:
                missing.append({
                    "document_type": dtype,
                    "label": label,
                    "action": "Upload document to Document Vault to reuse across applications."
                })
        return missing

    def create_application(self, opportunity_id: int) -> Dict[str, Any]:
        opp = Opportunity.objects.get(id=opportunity_id)
        app, created = Application.objects.get_or_create(
            user=self.user,
            opportunity=opp,
            defaults={'status': 'planning'}
        )
        if created:
            # Generate default requirements based on opportunity documents
            reqs = [
                ("Curriculum Vitae (CV)", "Tailored academic CV reflecting research and engineering experience.", True, "document"),
                ("Academic Transcript", "Official undergraduate degree transcript with course classifications.", True, "document"),
                ("Degree Certificate", "Certified Bachelor's degree certificate or statement of result.", True, "document"),
                ("Motivation Letter / Statement of Purpose", "Postgraduate motivation essay aligned with chosen field.", True, "essay"),
                ("Academic Reference Letter 1", "First academic referee endorsement from undergraduate professor.", True, "document"),
                ("Academic/Professional Reference Letter 2", "Second referee endorsement letter.", True, "document"),
                ("Passport Data Page", "Valid international passport copy.", True, "document"),
            ]
            for idx, (name, desc, mandatory, req_type) in enumerate(reqs, start=1):
                # Auto-link existing document if available in vault
                attached_doc = None
                if "CV" in name:
                    attached_doc = self.user.documents.filter(document_type='cv').first()
                elif "Transcript" in name:
                    attached_doc = self.user.documents.filter(document_type='transcript').first()
                elif "Passport" in name:
                    attached_doc = self.user.documents.filter(document_type='passport').first()
                elif "Certificate" in name:
                    attached_doc = self.user.documents.filter(document_type='degree_certificate').first()

                ApplicationRequirement.objects.create(
                    application=app,
                    name=name,
                    description=desc,
                    requirement_type=req_type,
                    is_mandatory=mandatory,
                    attached_document=attached_doc,
                    status='complete' if attached_doc else 'not_started',
                    order=idx
                )

            
            # Generate initial tasks
            ApplicationTask.objects.create(
                application=app,
                title="Review application requirements and deadline",
                description=f"Deadline is {opp.deadline.strftime('%b %d, %Y')}.",
                is_completed=False,
                due_date=timezone.now().date(),
                created_by_ai=True
            )
            ApplicationTask.objects.create(
                application=app,
                title="Draft Statement of Purpose with AI Assistant",
                description="Ground your motivation in your recorded projects and STAR stories.",
                is_completed=False,
                created_by_ai=True
            )

            # Audit log
            AIAuditLog.objects.create(
                user=self.user,
                action_type="create_application",
                provider="agent_orchestrator",
                summary=f"Created application workspace for {opp.title}",
                input_ref=f"Opportunity #{opp.id}",
                output_summary="Created workspace with 7 core requirements and initial tasks.",
                status="success"
            )

        return {
            "application_id": app.id,
            "opportunity": opp.title,
            "created": created,
            "status": app.get_status_display()
        }

    def draft_application_response(self, application_id: int, requirement_id: int, prompt_context: str = "") -> Dict[str, Any]:
        app = Application.objects.get(id=application_id, user=self.user)
        req = ApplicationRequirement.objects.get(id=requirement_id, application=app)
        
        draft = self.ai_service.draft_essay_response(
            user=self.user,
            opportunity=app.opportunity,
            question_title=req.name,
            prompt_context=prompt_context
        )

        req.draft_response = draft.draft_content
        req.status = 'needs_review'
        req.ai_grounding_notes = (
            f"Grounding Evidence: Used facts ({', '.join(draft.used_facts)}). "
            f"Stories referenced: ({', '.join(draft.used_stories)})."
        )
        req.save()

        return {
            "requirement_id": req.id,
            "draft_content": draft.draft_content,
            "word_count": draft.word_count,
            "used_facts": draft.used_facts,
            "used_stories": draft.used_stories,
            "improvement_notes": draft.improvement_notes
        }

    def request_user_approval(self, action_type: str, title: str, description: str, payload: dict) -> AgentAction:
        """
        Enforces human-in-the-loop: creates an AgentAction in PENDING state.
        Never executes consequential action autonomously.
        """
        action = AgentAction.objects.create(
            user=self.user,
            action_type=action_type,
            title=title,
            description=description,
            payload=payload,
            status='pending'
        )

        Notification.objects.create(
            user=self.user,
            notification_type='action_approval_needed',
            title=f"Approval Required: {title}",
            message=description,
            action_url=f"/agent/actions/{action.id}/"
        )

        return action

    # ---------------- Conversational Agent Processor ----------------
    def process_message(self, message: str) -> Dict[str, Any]:
        msg_lower = message.lower()
        
        # Intent classification & tool dispatching
        if "find" in msg_lower or "search" in msg_lower or "opportunity" in msg_lower or "scholarship" in msg_lower or "msc" in msg_lower:
            country = "Germany" if "germany" in msg_lower else ("UK" if "uk" in msg_lower or "britain" in msg_lower else ("Europe" if "europe" in msg_lower else ""))
            results = self.search_opportunities(country=country)
            
            summary_cards = []
            for r in results[:4]:
                summary_cards.append(f"• **{r['title']}** ({r['provider']}, {r['country']}) - {r['funding_type']} | Deadline: {r['deadline']}")
            
            text = (
                f"I found {len(results)} active opportunities matching your criteria:\n\n"
                + "\n".join(summary_cards) +
                "\n\nYou can click any opportunity in the **Discover** tab to assess your detailed eligibility or click **Start Application** to open a dedicated workspace."
            )
            return {
                "response": text,
                "tool_used": "search_opportunities",
                "data": results
            }

        elif "missing" in msg_lower or "document" in msg_lower:
            missing = self.list_missing_documents()
            if missing:
                items = [f"• **{m['label']}**: {m['action']}" for m in missing]
                text = "Here are the recommended documents missing from your Document Vault:\n\n" + "\n".join(items)
            else:
                text = "All core documents (CV, Transcript, Passport, Recommendation Letters) are present in your Document Vault!"
            return {
                "response": text,
                "tool_used": "list_missing_documents",
                "data": missing
            }

        elif "verify" in msg_lower or "portal" in msg_lower or "launch" in msg_lower or ("apply" in msg_lower and any(k in msg_lower for k in ["link", "check", "scan", "active", "where"])):
            # Find matching opportunity if mentioned in prompt
            opp = None
            for o in Opportunity.objects.filter(status='active'):
                if o.title.lower() in msg_lower or o.provider.lower() in msg_lower or (o.country and o.country.lower() in msg_lower):
                    opp = o
                    break
            if not opp:
                opp = Opportunity.objects.filter(status='active').first()

            if opp:
                v_res = self.verify_portal_for_application(opp.id)
                status_icon = "🟢" if v_res["is_live"] else "🔴"
                text = (
                    f"{status_icon} **Live Portal Verification: {opp.title}**\n\n"
                    f"• **Target Portal**: [{v_res['application_url']}]({v_res['application_url']})\n"
                    f"• **Live HTTP Status**: `{v_res['status_code']} {'Active & Responding' if v_res['is_live'] else 'Connection Checked'}`\n"
                    f"• **Portal Type**: {v_res['portal_type']}\n"
                    f"• **AI Application Readiness**: **{v_res['ai_readiness']}**\n"
                    f"• **Intake Cycle**: {opp.cycle_name} ({v_res['cycle_badge']['label']})\n\n"
                    f"**Agent Verification Analysis**:\n{v_res['summary']}\n\n"
                    f"{'✅ Your Document Vault is ready for autonomous application mapping.' if v_res['can_auto_prepare'] else 'ℹ️ Note: Upload your CV and academic transcripts to the Document Vault to allow the AI agent to map your documents directly into this portal.'}"
                )
                return {
                    "response": text,
                    "tool_used": "verify_portal_for_application",
                    "data": v_res
                }

        elif "submit" in msg_lower:
            text = (
                "To submit your application, open your **Application Workspace** and access the **Fast Portal Dossier (Copy Hub)**. "
                "From there, use the **Apply on Official Portal** link to upload your verified documents and submit directly to the institution."
            )
            return {
                "response": text,
                "tool_used": "guidance_submission",
                "data": {}
            }

        else:
            profile_summary = self.kb.get_summary_text()
            text = (
                f"Hello! I am your Flii Application Agent. I have your verified applicant profile loaded:\n\n"
                f"*{profile_summary[:180]}...*\n\n"
                "I can help you:\n"
                "1. **Discover verified scholarships** (e.g. 'Find fully funded MSc in Germany')\n"
                "2. **Check your eligibility** and identify missing documents\n"
                "3. **Draft motivation essays** grounded strictly in your real projects and STAR stories\n"
                "4. **Track application deadlines and tasks**"
            )
            return {
                "response": text,
                "tool_used": "get_applicant_profile",
                "data": {}
            }
