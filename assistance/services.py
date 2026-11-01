import logging
from decimal import Decimal
from typing import List, Dict, Any, Tuple, Optional
from django.utils import timezone
from .models import AssistancePackage, AssistanceBooking
from notifications.models import Notification

logger = logging.getLogger(__name__)

# Proposed Pay-Per-Application Service Catalogue
# Fully configurable through Django Admin
DEFAULT_PACKAGES = [
    {
        "name": "Scholarship Eligibility and Requirements Assessment",
        "slug": "eligibility-requirements-assessment",
        "category": "eligibility_assessment",
        "service_type": "essay_review",
        "delivery_type": "hybrid",
        "requires_human_review": True,
        "tagline": "In-depth criteria audit against official scholarship guidelines.",
        "description": "Comprehensive evaluation of your academic qualifications, GPA conversion, work experience, and language certifications against target scholarship requirements. Identifies disqualification risks and provides an actionable pre-application checklist.",
        "price": Decimal("2000.00"),
        "price_max": None,
        "currency": "NGN",
        "estimated_delivery_time": "24–48 hours",
        "turnaround_days": 2,
        "service_instructions": "Provide your degree background, CGPA, target scholarship, and any language test results or waivers.",
        "document_requirements": "Academic transcript, Degree certificate, Target scholarship link or name.",
        "badge": "Eligibility Audit",
        "icon": "shield-check",
        "order": 1,
        "features": [
            "Official selection criteria breakdown",
            "Academic qualification & CGPA threshold check",
            "Disqualification risk detection",
            "Recommended alternative scholarship shortlists",
            "Actionable pre-application roadmap"
        ]
    },
    {
        "name": "CV Review and Improvement",
        "slug": "cv-review-improvement",
        "category": "cv_review",
        "service_type": "essay_review",
        "delivery_type": "human_review",
        "requires_human_review": True,
        "tagline": "Transform your resume into a global academic standard CV.",
        "description": "Detailed line-by-line review of your academic CV or Europass resume by a verified postgraduate scholar. We optimize structure, highlight research achievements, eliminate red flags, and ensure alignment with global funding standards.",
        "price": Decimal("5000.00"),
        "price_max": None,
        "currency": "NGN",
        "estimated_delivery_time": "48 hours",
        "turnaround_days": 2,
        "service_instructions": "Upload your current CV/Resume (Word or PDF). Highlight any publications, projects, or leadership roles.",
        "document_requirements": "Current draft CV/Resume, Target degree and country.",
        "badge": "High Demand",
        "icon": "file-text",
        "order": 2,
        "features": [
            "Europass & Global academic CV formatting",
            "Impact-driven phrasing with STAR metrics",
            "Removal of red flags & irrelevant details",
            "Annotated markup with direct phrasing suggestions",
            "1 round of follow-up adjustments"
        ]
    },
    {
        "name": "Motivation Letter Review",
        "slug": "motivation-letter-review",
        "category": "motivation_letter",
        "service_type": "essay_review",
        "delivery_type": "human_review",
        "requires_human_review": True,
        "tagline": "Admissions-grade critique for European & Commonwealth scholarships.",
        "description": "Line-by-line critical review of your scholarship motivation letter. We evaluate thematic flow, academic justification, genuine leadership narratives, and ensure your essay directly answers every required prompt without generic clichés.",
        "price": Decimal("5000.00"),
        "price_max": Decimal("8000.00"),
        "currency": "NGN",
        "estimated_delivery_time": "3 business days",
        "turnaround_days": 3,
        "service_instructions": "Upload your motivation letter draft along with the scholarship guidelines and specific prompt questions.",
        "document_requirements": "Draft motivation letter (Word or PDF), Scholarship prompt instructions.",
        "badge": "Most Popular",
        "icon": "file-check-2",
        "order": 3,
        "features": [
            "Line-by-line structural, tone, and grammar refinement",
            "Alignment check against selection committee rubrics",
            "Strengthening of academic justification and future career plan",
            "Detection of unsupported claims or generic clichés",
            "Annotated deliverable with substantive inline comments"
        ]
    },
    {
        "name": "Personal Statement Review",
        "slug": "personal-statement-review",
        "category": "personal_statement",
        "service_type": "essay_review",
        "delivery_type": "human_review",
        "requires_human_review": True,
        "tagline": "Craft a persuasive, authentic narrative of resilience and ambition.",
        "description": "Rigorous review of your postgraduate personal statement. Focuses on authentic personal storytelling, connecting past obstacles with future academic impact, and presenting a compelling hook that captures the admissions committee's attention.",
        "price": Decimal("5000.00"),
        "price_max": Decimal("8000.00"),
        "currency": "NGN",
        "estimated_delivery_time": "3 business days",
        "turnaround_days": 3,
        "service_instructions": "Upload your personal statement draft and indicate which university and programme you are applying for.",
        "document_requirements": "Draft personal statement, target university programme link.",
        "badge": "Top Rated",
        "icon": "pen-tool",
        "order": 4,
        "features": [
            "Opening hook & narrative arc refinement",
            "Authentic personal voice preservation",
            "STAR methodology alignment for achievements",
            "Elimination of repetitive or unverified claims",
            "Direct comments and suggested phrasing"
        ]
    },
    {
        "name": "Full Application Document Review",
        "slug": "full-application-review",
        "category": "full_application_review",
        "service_type": "full_audit",
        "delivery_type": "human_review",
        "requires_human_review": True,
        "tagline": "End-to-end dossier audit: CV, Motivation, Transcripts & References.",
        "description": "Our complete pre-submission safety audit. A qualified reviewer checks your entire application bundle (CV, Statement of Purpose, Recommender Guidance, Transcripts) to ensure 100% cohesion, zero conflicting information, and maximum impact.",
        "price": Decimal("10000.00"),
        "price_max": Decimal("15000.00"),
        "currency": "NGN",
        "estimated_delivery_time": "4 business days",
        "turnaround_days": 4,
        "service_instructions": "Upload all required documents for your chosen scholarship application in one bundle.",
        "document_requirements": "CV, Motivation Letter, Transcripts, Recommender letters or notes, Scholarship application link.",
        "badge": "Comprehensive",
        "icon": "layers",
        "order": 5,
        "features": [
            "Complete package consistency and narrative cohesion audit",
            "Detailed line-by-line markup on all written documents",
            "Verification of all mandatory checklist requirements",
            "Identification of conflicting dates or ungrounded claims",
            "Final readiness score & debrief action plan"
        ]
    },
    {
        "name": "Application Preparation Support",
        "slug": "application-prep-support",
        "category": "prep_support",
        "service_type": "custom",
        "delivery_type": "hybrid",
        "requires_human_review": True,
        "tagline": "Hands-on step-by-step guidance through submission.",
        "description": "Dedicated end-to-end application partnership for high-stakes scholarships. Includes roadmap planning, drafting assistance, document verification, portal entry guidance, and pre-submission validation with a senior scholarship mentor.",
        "price": Decimal("15000.00"),
        "price_max": Decimal("25000.00"),
        "currency": "NGN",
        "estimated_delivery_time": "7-10 days",
        "turnaround_days": 7,
        "service_instructions": "Describe your target scholarship, deadlines, and upload your current academic profile documents.",
        "document_requirements": "Full academic history, transcripts, target scholarship details.",
        "badge": "VIP Mentorship",
        "icon": "sparkles",
        "order": 6,
        "features": [
            "Dedicated senior reviewer assigned throughout your application cycle",
            "Tailored milestone timeline and deadline accountability",
            "Unlimited feedback rounds on essays and CV",
            "Application portal question-by-question review",
            "Pre-submission final sign-off"
        ]
    },
]

LEGACY_INACTIVE_SLUGS = [
    'sop-essay-review',
    'one-on-one-strategy',
    'mock-interview-prep',
    'full-application-audit',
    'research-proposal-review',
]


def ensure_default_packages_seeded():
    """
    Seeds default service catalogue items if not already present.
    Configurable via Django Admin.
    """
    # Deactivate obsolete/legacy test packages so only current catalogue is active
    AssistancePackage.objects.filter(slug__in=LEGACY_INACTIVE_SLUGS).update(is_active=False)

    for pkg_data in DEFAULT_PACKAGES:
        AssistancePackage.objects.update_or_create(
            slug=pkg_data["slug"],
            defaults=pkg_data
        )


def notify_booking_created(booking: AssistanceBooking):
    """
    Dispatches notifications when an applicant books a paid service.
    """
    # 1. Notify Applicant
    Notification.objects.create(
        user=booking.user,
        title=f"📋 Assistance Booked: {booking.package_title} (#{booking.order_number})",
        message=f"Order #{booking.order_number} has been placed. Current status: {booking.get_status_display()}.",
        notification_type='system'
    )

    # 2. Notify Administrators / Mentors
    from django.contrib.auth import get_user_model
    User = get_user_model()
    admin_users = User.objects.filter(is_staff=True)
    for admin_user in admin_users:
        Notification.objects.create(
            user=admin_user,
            title=f"🔔 New Paid Assistance Request: #{booking.order_number}",
            message=f"Applicant {booking.user.get_full_name() or booking.user.email} placed order #{booking.order_number} ({booking.package_title} - ₦{booking.price:,.0f}).",
            notification_type='system'
        )


def notify_booking_status_updated(booking: AssistanceBooking, previous_status: str):
    """
    Dispatches alerts upon service order status changes.
    """
    if previous_status == booking.status:
        return

    Notification.objects.create(
        user=booking.user,
        title=f"Update on Order #{booking.order_number}",
        message=f"Your service order status has updated to: '{booking.get_status_display()}'.",
        notification_type='system'
    )


class ServiceOrderService:
    """
    Management service handling Pay-Per-Application order lifecycle, reviewer assignments,
    and server-side payment confirmations.
    """

    @classmethod
    def confirm_service_payment(cls, reference: str) -> Tuple[bool, str]:
        """
        Server-side confirmation of service order payment.
        """
        booking = AssistanceBooking.objects.filter(payment_reference=reference).first()
        if not booking:
            # Check via linked PaymentTransaction
            from subscriptions.models import PaymentTransaction
            tx = PaymentTransaction.objects.filter(reference=reference).first()
            if tx and tx.service_order_id:
                booking = AssistanceBooking.objects.filter(id=tx.service_order_id).first()

        if not booking:
            return False, f"No service order found for reference {reference}"

        if booking.payment_status == 'paid':
            return True, "Payment was already confirmed."

        booking.payment_status = 'paid'
        booking.status = 'awaiting_assignment' if booking.package and booking.package.requires_human_review else 'in_progress'
        booking.save(update_fields=['payment_status', 'status', 'updated_at'])

        # Notify applicant
        Notification.objects.create(
            user=booking.user,
            title=f"💳 Payment Confirmed: Order #{booking.order_number}",
            message=f"Your payment of ₦{booking.price:,.0f} for {booking.package_title} was verified. Our team is preparing your review.",
            notification_type='system'
        )

        return True, "Payment verified and order queued."

    @classmethod
    def assign_reviewer(cls, booking: AssistanceBooking, reviewer_user, admin_user=None) -> bool:
        """
        Assigns an order to an internal reviewer.
        """
        booking.assigned_reviewer = reviewer_user
        booking.assigned_admin = reviewer_user
        booking.status = 'assigned'
        booking.save(update_fields=['assigned_reviewer', 'assigned_admin', 'status', 'updated_at'])

        # Notify reviewer
        Notification.objects.create(
            user=reviewer_user,
            title=f"📝 New Order Assigned: #{booking.order_number}",
            message=f"You have been assigned to review {booking.package_title} for {booking.user.get_full_name() or booking.user.email}.",
            notification_type='system'
        )

        # Notify applicant
        Notification.objects.create(
            user=booking.user,
            title=f"Reviewer Assigned: Order #{booking.order_number}",
            message=f"A qualified reviewer has been assigned to your order '{booking.package_title}'. Work is commencing.",
            notification_type='system'
        )
        return True

    @classmethod
    def complete_order(cls, booking: AssistanceBooking, feedback: str, deliverable_file=None) -> bool:
        """
        Marks work as completed and delivers review to applicant.
        """
        booking.status = 'completed'
        booking.completed_at = timezone.now()
        booking.deliverable_feedback = feedback
        if deliverable_file:
            booking.deliverable_file = deliverable_file
        booking.save()

        Notification.objects.create(
            user=booking.user,
            title=f"🎉 Order Completed: #{booking.order_number}",
            message=f"Your completed review for {booking.package_title} is ready to view in your dashboard.",
            notification_type='system'
        )
        return True
