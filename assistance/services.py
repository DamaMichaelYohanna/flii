import logging
from typing import List, Dict, Any
from .models import AssistancePackage, AssistanceBooking
from notifications.models import Notification

logger = logging.getLogger(__name__)

DEFAULT_PACKAGES = [
    {
        "name": "Personal Statement & SOP Line-by-Line Polish",
        "slug": "sop-essay-review",
        "service_type": "essay_review",
        "tagline": "Admissions-grade feedback, structural rigor, and tone perfection.",
        "description": "Comprehensive line-by-line critique of your Statement of Purpose, Motivation Letter, or Scholarship Essays. Reviewed by senior academic scholars who evaluate alignment against scholarship criteria, persuasiveness, and authentic storytelling.",
        "price": 49.00,
        "currency": "USD",
        "turnaround_days": 3,
        "badge": "Popular",
        "icon": "file-check-2",
        "order": 1,
        "features": [
            "Line-by-line editorial feedback and word choice refinement",
            "Scholarship selection rubric & criteria alignment check",
            "Clear diagnostic report highlighting strengths and red flags",
            "Annotated PDF / Word deliverable ready within 72 hours",
            "1 round of follow-up Q&A directly with the reviewer"
        ]
    },
    {
        "name": "1-on-1 Scholarship Strategy & Profile Diagnostic",
        "slug": "one-on-one-strategy",
        "service_type": "advisory_call",
        "tagline": "45-minute live video session with platform admin & scholarship mentors.",
        "description": "Direct, face-to-face tactical guidance. We review your academic history, identify your competitive edge, determine top-fit European and global funding opportunities, and map out a strategic timeline to maximize acceptance.",
        "price": 69.00,
        "currency": "USD",
        "turnaround_days": 2,
        "badge": "Live Advisory",
        "icon": "video",
        "order": 2,
        "features": [
            "45-minute 1-on-1 private video session via Google Meet / Zoom",
            "Target scholarship shortlist validation (Erasmus, DAAD, etc.)",
            "Profile gap analysis and framing of non-traditional experiences",
            "Step-by-step roadmap tailored to your specific deadlines",
            "Full call recording and written action summary"
        ]
    },
    {
        "name": "Scholarship Mock Interview & Defense",
        "slug": "mock-interview-prep",
        "service_type": "mock_interview",
        "tagline": "Realistic 60-minute panel simulation with instant scoring.",
        "description": "Prepare for high-stakes scholarship selection panels. We conduct a simulated scholarship committee interview based on your real application materials, probe your research motivation, and coach you on delivery, composure, and STAR methodology.",
        "price": 79.00,
        "currency": "USD",
        "turnaround_days": 3,
        "badge": "High Impact",
        "icon": "mic-2",
        "order": 3,
        "features": [
            "60-minute simulated panel interview with personalized questions",
            "Deep drill-down on research proposals, future goals, and leadership",
            "Real-time verbal feedback on body language, timing, and clarity",
            "Standard & curveball scholarship interview question bank",
            "Detailed written rubric score and improvement notes"
        ]
    },
    {
        "name": "Comprehensive Full Application Audit & Polish",
        "slug": "full-application-audit",
        "service_type": "full_audit",
        "tagline": "Complete end-to-end packet review plus 45-minute debrief.",
        "description": "Our most thorough pre-submission safeguard. We review your entire application packet—CV/Resume, SOP, Research Proposal, Recommender guidance notes, and transcript narrative—followed by a live 45-minute debrief call.",
        "price": 129.00,
        "currency": "USD",
        "turnaround_days": 4,
        "badge": "All-Inclusive",
        "icon": "shield-check",
        "order": 4,
        "features": [
            "Full packet review: CV, SOP, Cover Letters & Proposal check",
            "Cohesion audit: Ensuring all application pieces reinforce one narrative",
            "Detailed line-by-line markup on all narrative documents",
            "45-minute live debrief video session to address every detail",
            "Final submission readiness stamp & peace of mind"
        ]
    },
]


def ensure_default_packages_seeded():
    """
    Seeds default assistance packages if not already present.
    """
    created_count = 0
    for pkg_data in DEFAULT_PACKAGES:
        obj, created = AssistancePackage.objects.get_or_create(
            slug=pkg_data["slug"],
            defaults=pkg_data
        )
        if created:
            created_count += 1
    return created_count


def notify_booking_created(booking: AssistanceBooking):
    """
    Sends in-app notifications to applicant and admins.
    """
    from accounts.models import User

    # Applicant confirmation notification
    Notification.objects.create(
        user=booking.user,
        notification_type='system',
        title=f"Assistance Booked: {booking.package_title}",
        message=f"Your booking has been received ({booking.urgency}). Our admin team will review your submission and confirm scheduling shortly.",
        action_url=f"/assistance/booking/{booking.id}/"
    )

    # Notify all staff/admins
    admins = User.objects.filter(is_staff=True)
    for admin_user in admins:
        Notification.objects.create(
            user=admin_user,
            notification_type='system',
            title=f"New Paid Assistance Booking: #{booking.id}",
            message=f"{booking.user.get_full_name() or booking.user.email} requested {booking.package_title} (${booking.price}).",
            action_url=f"/assistance/admin/booking/{booking.id}/"
        )


def notify_booking_status_updated(booking: AssistanceBooking, old_status: str):
    """
    Sends notification to applicant when admin updates status, meeting link, or deliverables.
    """
    if booking.status == 'scheduled' and booking.meeting_link:
        Notification.objects.create(
            user=booking.user,
            notification_type='system',
            title=f"Live Session Scheduled: {booking.package_title}",
            message=f"Your advisory session is confirmed for {booking.scheduled_at.strftime('%b %d, %Y at %H:%M UTC') if booking.scheduled_at else 'your requested slot'}. Meeting link is ready.",
            action_url=f"/assistance/booking/{booking.id}/"
        )
    elif booking.status == 'completed':
        Notification.objects.create(
            user=booking.user,
            notification_type='system',
            title=f"Assistance Deliverable Ready: {booking.package_title}",
            message="Your review is complete! Your reviewed documents and admin expert feedback are ready to download.",
            action_url=f"/assistance/booking/{booking.id}/"
        )
    elif booking.status != old_status:
        Notification.objects.create(
            user=booking.user,
            notification_type='system',
            title=f"Booking Update: {booking.package_title}",
            message=f"Status updated to '{booking.get_status_display()}'.",
            action_url=f"/assistance/booking/{booking.id}/"
        )
