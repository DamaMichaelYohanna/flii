from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class RequirementAssessment(BaseModel):
    requirement_name: str = Field(description="Name of requirement e.g. Academic Qualification, Nationality, English Proficiency")
    status: Literal["satisfied", "needs_clarification", "unmet"] = Field(description="Verdict for this specific requirement")
    applicant_evidence: str = Field(description="Verified fact from applicant profile supporting this status")
    explanation: str = Field(description="Clear explanation grounded in official scholarship rules")

class EligibilityResult(BaseModel):
    eligibility_status: Literal["confirmed_eligible", "likely_eligible", "needs_clarification", "likely_ineligible", "ineligible"] = Field(
        description="Overall profile eligibility classification"
    )
    profile_fit_score: int = Field(ge=0, le=100, description="Profile alignment score (0-100) based on criteria met")
    matched_requirements: List[RequirementAssessment] = Field(default_factory=list)
    unresolved_requirements: List[RequirementAssessment] = Field(default_factory=list)
    failed_requirements: List[RequirementAssessment] = Field(default_factory=list)
    missing_documents: List[str] = Field(default_factory=list)
    summary_explanation: str = Field(description="Transparent summary of why applicant matches or has blockers")

class EssayDraftResult(BaseModel):
    question_title: str
    draft_content: str = Field(description="High-quality essay draft grounded purely on applicant profile and stories")
    word_count: int
    used_stories: List[str] = Field(default_factory=list, description="Titles of stories referenced")
    used_facts: List[str] = Field(default_factory=list, description="Profile facts used in the text")
    unsupported_claims_flagged: List[str] = Field(default_factory=list, description="Any items requiring applicant verification")
    improvement_notes: str = Field(default="", description="Suggestions for applicant to personalize further")

class AgentStepResult(BaseModel):
    thought: str
    tool_called: Optional[str] = None
    tool_args: dict = Field(default_factory=dict)
    response_message: str
    requires_human_approval: bool = False
    action_type: Optional[str] = None
    action_payload: Optional[dict] = None

class OpportunityExtractionSchema(BaseModel):
    title: str = Field(description="Official name of the scholarship or Master's programme")
    provider: str = Field(description="Funding agency, government body, or foundation")
    university: str = Field(default="", description="Specific university or consortium (if applicable)")
    country: str = Field(description="Host country or European Union")
    degree_level: Literal["masters", "phd", "fellowship", "bachelors", "postdoc"] = Field(default="masters")
    field_of_study: str = Field(description="Eligible academic disciplines")
    description: str = Field(description="Overview of the award and programme")
    funding_type: Literal["fully_funded", "partial", "tuition_waiver", "stipend_only"] = Field(default="fully_funded")
    funding_details: str = Field(description="Detailed allowance breakdown (stipend, tuition, flights, health insurance)")
    eligibility_summary: str = Field(description="Bulleted summary of eligibility criteria")
    application_url: str = Field(default="", description="Direct link to portal")
    official_source_url: str = Field(default="", description="Official documentation link")
    opening_date_iso: Optional[str] = Field(default=None, description="Application opening date in YYYY-MM-DD format (if specified)")
    deadline_iso: str = Field(default="2026-12-31", description="Application deadline in YYYY-MM-DD format")
    cycle_name: str = Field(default="2026/2027 Academic Year", description="Academic intake or cycle name")
    language_requirement: str = Field(description="English language test score or waiver details")
    academic_requirement: str = Field(description="Minimum GPA or degree classification")
    nationality_requirement: str = Field(description="Eligible countries or target regions")
    documents_required: str = Field(description="Mandatory documents to submit")
    application_fee: str = Field(default="Free / €0")


class PortalVerificationSchema(BaseModel):
    is_live_and_active: bool = Field(description="Whether the portal page is active, valid, and responding")
    portal_type: Literal["direct_portal", "external_portal", "nomination_required", "email_submission"] = Field(
        default="direct_portal",
        description="Type of submission system: direct form, external portal, nomination, or email"
    )
    ai_application_readiness: Literal["ready", "requires_login", "not_yet_open", "manual_only"] = Field(
        default="ready",
        description="Whether an AI agent or applicant can immediately apply, must login, or must wait until opening"
    )
    direct_apply_url: Optional[str] = Field(
        default=None,
        description="Exact direct online application link discovered on the page (if distinct from info page)"
    )
    detected_opening_date_iso: Optional[str] = Field(
        default=None,
        description="Discovered opening date in YYYY-MM-DD format"
    )
    detected_closing_date_iso: Optional[str] = Field(
        default=None,
        description="Discovered closing deadline date in YYYY-MM-DD format"
    )
    cycle_name: Optional[str] = Field(
        default="2026/2027 Academic Year",
        description="Active application cycle name"
    )
    verification_summary: str = Field(
        description="Concise analysis of portal accessibility, submission instructions, and readiness for AI agent"
    )
