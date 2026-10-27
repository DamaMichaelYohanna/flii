from decimal import Decimal
import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.db.models import Q

from .models import AssistancePackage, AssistanceBooking
from .services import (
    ensure_default_packages_seeded,
    notify_booking_created,
    notify_booking_status_updated
)
from applications.models import Application
from documents.models import Document


def assistance_home(request):
    """
    Public / Applicant landing page displaying all verified paid assistance packages,
    mentorship methodology, testimonials, and FAQs.
    """
    ensure_default_packages_seeded()
    packages = AssistancePackage.objects.filter(is_active=True).order_by('order', 'price')
    
    user_bookings_count = 0
    if request.user.is_authenticated:
        user_bookings_count = AssistanceBooking.objects.filter(user=request.user).count()

    context = {
        'packages': packages,
        'user_bookings_count': user_bookings_count,
    }
    return render(request, 'assistance/home.html', context)


@login_required
def book_assistance(request, package_slug=None):
    """
    Interactive multi-step booking form for applicants to request paid assistance
    from platform administrators/mentors.
    """
    ensure_default_packages_seeded()
    packages = AssistancePackage.objects.filter(is_active=True).order_by('order', 'price')

    selected_package = None
    target_slug = package_slug or request.GET.get('package')
    if target_slug:
        selected_package = packages.filter(slug=target_slug).first()

    # Pre-select application if passed via query params
    selected_app_id = request.GET.get('app_id')
    user_applications = request.user.applications.select_related('opportunity').all()
    user_documents = request.user.documents.all()

    if request.method == 'POST':
        package_id = request.POST.get('package_id')
        package = get_object_or_404(AssistancePackage, id=package_id, is_active=True)

        app_id = request.POST.get('application_id')
        app_obj = None
        if app_id:
            app_obj = user_applications.filter(id=app_id).first()

        target_scholarship = request.POST.get('target_scholarship', '').strip()
        if app_obj and not target_scholarship:
            target_scholarship = app_obj.opportunity.title

        target_university = request.POST.get('target_university', '').strip()
        urgency = request.POST.get('urgency', 'standard')
        
        # Calculate price based on urgency
        base_price = package.price
        if urgency == 'priority':
            final_price = (base_price * Decimal('1.25')).quantize(Decimal('0.01'))
        elif urgency == 'rush':
            final_price = (base_price * Decimal('1.50')).quantize(Decimal('0.01'))
        else:
            final_price = base_price

        # Scheduling preference
        preferred_date_raw = request.POST.get('preferred_date', '').strip()
        preferred_date = None
        if preferred_date_raw:
            try:
                preferred_date = datetime.datetime.strptime(preferred_date_raw, '%Y-%m-%d').date()
            except ValueError:
                preferred_date = None

        preferred_time_slot = request.POST.get('preferred_time_slot', 'afternoon')
        applicant_notes = request.POST.get('applicant_notes', '').strip()
        contact_phone = request.POST.get('contact_phone', '').strip()
        preferred_contact_method = request.POST.get('preferred_contact_method', 'google_meet')

        # Document attachment
        attached_file = request.FILES.get('attached_document')
        vault_doc_id = request.POST.get('document_vault_ref')
        vault_doc = None
        if vault_doc_id:
            vault_doc = user_documents.filter(id=vault_doc_id).first()

        if not applicant_notes:
            messages.error(request, "Please provide background details and specific goals for the admin team.")
            return render(request, 'assistance/book.html', {
                'packages': packages,
                'selected_package': package,
                'user_applications': user_applications,
                'user_documents': user_documents,
            })

        booking = AssistanceBooking.objects.create(
            user=request.user,
            package=package,
            package_title=package.name,
            service_type=package.service_type,
            application=app_obj,
            target_scholarship=target_scholarship,
            target_university=target_university,
            price=final_price,
            currency=package.currency,
            urgency=urgency,
            preferred_date=preferred_date,
            preferred_time_slot=preferred_time_slot,
            applicant_notes=applicant_notes,
            attached_document=attached_file,
            document_vault_ref=vault_doc,
            contact_email=request.user.email,
            contact_phone=contact_phone,
            preferred_contact_method=preferred_contact_method,
            status='pending_payment',
            payment_status='unpaid'
        )

        notify_booking_created(booking)

        messages.success(
            request,
            f"🎉 Paid assistance booking created! Your request for '{package.name}' (${final_price}) is registered."
        )
        return redirect('assistance:booking_detail', pk=booking.id)

    context = {
        'packages': packages,
        'selected_package': selected_package,
        'selected_app_id': selected_app_id,
        'user_applications': user_applications,
        'user_documents': user_documents,
    }
    return render(request, 'assistance/book.html', context)


@login_required
def my_bookings(request):
    """
    List of all paid assistance bookings for the authenticated applicant.
    """
    filter_status = request.GET.get('status', 'all')
    qs = AssistanceBooking.objects.filter(user=request.user).select_related('package', 'application')

    if filter_status == 'active':
        qs = qs.exclude(status__in=['completed', 'cancelled'])
    elif filter_status == 'completed':
        qs = qs.filter(status='completed')

    context = {
        'bookings': qs,
        'current_filter': filter_status,
        'total_count': qs.count(),
    }
    return render(request, 'assistance/my_bookings.html', context)


@login_required
def booking_detail(request, pk):
    """
    Detail page for an assistance booking:
    Status timeline, payment instructions/reference submission, meeting link, and downloadable deliverable.
    """
    if request.user.is_staff:
        booking = get_object_or_404(AssistanceBooking.objects.select_related('user', 'package', 'application'), pk=pk)
    else:
        booking = get_object_or_404(AssistanceBooking.objects.select_related('package', 'application'), pk=pk, user=request.user)

    context = {
        'booking': booking,
    }
    return render(request, 'assistance/booking_detail.html', context)


@login_required
def booking_payment_submit(request, pk):
    """
    Applicant submits their payment proof or transaction reference.
    """
    booking = get_object_or_404(AssistanceBooking, pk=pk, user=request.user)

    if request.method == 'POST':
        payment_reference = request.POST.get('payment_reference', '').strip()
        payment_proof = request.FILES.get('payment_proof')

        if not payment_reference and not payment_proof:
            messages.error(request, "Please enter a transaction reference ID or upload payment proof.")
            return redirect('assistance:booking_detail', pk=booking.id)

        if payment_reference:
            booking.payment_reference = payment_reference
        if payment_proof:
            booking.payment_proof = payment_proof

        booking.payment_status = 'pending_verification'
        booking.save(update_fields=['payment_reference', 'payment_proof', 'payment_status', 'updated_at'])

        messages.success(
            request,
            "✅ Payment information received! Our admin team will verify it and confirm your booking."
        )

    return redirect('assistance:booking_detail', pk=booking.id)


# ==========================================
# Platform Admin Hub & Management Views
# ==========================================

@login_required
def admin_bookings_hub(request):
    """
    Staff / Platform Admin Dashboard for tracking and managing all user assistance bookings.
    """
    if not request.user.is_staff:
        messages.warning(request, "Staff privileges required to access the Assistance Management Hub.")
        return redirect('dashboard:index')

    status_filter = request.GET.get('status', 'all')
    search_q = request.GET.get('q', '').strip()

    qs = AssistanceBooking.objects.select_related('user', 'package', 'application').order_by('-created_at')

    if status_filter != 'all':
        qs = qs.filter(status=status_filter)

    if search_q:
        qs = qs.filter(
            Q(user__email__icontains=search_q) |
            Q(user__first_name__icontains=search_q) |
            Q(user__last_name__icontains=search_q) |
            Q(package_title__icontains=search_q) |
            Q(target_scholarship__icontains=search_q) |
            Q(payment_reference__icontains=search_q)
        )

    # Metrics
    all_bookings = AssistanceBooking.objects.all()
    total_count = all_bookings.count()
    pending_payment_count = all_bookings.filter(status='pending_payment').count()
    in_review_count = all_bookings.filter(status='in_review').count()
    scheduled_count = all_bookings.filter(status='scheduled').count()
    completed_count = all_bookings.filter(status='completed').count()

    context = {
        'bookings': qs,
        'current_status': status_filter,
        'search_q': search_q,
        'total_count': total_count,
        'pending_payment_count': pending_payment_count,
        'in_review_count': in_review_count,
        'scheduled_count': scheduled_count,
        'completed_count': completed_count,
    }
    return render(request, 'assistance/admin_hub.html', context)


@login_required
def admin_booking_detail(request, pk):
    """
    Staff workbench for fulfilling a single user booking:
    - Confirm payment
    - Set meeting link (Google Meet / Zoom)
    - Schedule time
    - Upload deliverable file and write expert review feedback
    - Change status to completed
    """
    if not request.user.is_staff:
        return HttpResponseForbidden("Unauthorized")

    booking = get_object_or_404(AssistanceBooking.objects.select_related('user', 'package', 'application'), pk=pk)

    if request.method == 'POST':
        old_status = booking.status
        new_status = request.POST.get('status', booking.status)
        new_payment_status = request.POST.get('payment_status', booking.payment_status)
        meeting_link = request.POST.get('meeting_link', '').strip()
        admin_notes = request.POST.get('admin_notes', '').strip()
        deliverable_feedback = request.POST.get('deliverable_feedback', '').strip()
        deliverable_file = request.FILES.get('deliverable_file')

        scheduled_at_raw = request.POST.get('scheduled_at', '').strip()
        if scheduled_at_raw:
            try:
                dt = datetime.datetime.fromisoformat(scheduled_at_raw)
                booking.scheduled_at = timezone.make_aware(dt) if timezone.is_naive(dt) else dt
            except Exception:
                pass

        booking.status = new_status
        booking.payment_status = new_payment_status
        booking.meeting_link = meeting_link
        booking.admin_notes = admin_notes
        booking.deliverable_feedback = deliverable_feedback

        if deliverable_file:
            booking.deliverable_file = deliverable_file

        if new_status == 'completed' and not booking.completed_at:
            booking.completed_at = timezone.now()

        booking.assigned_admin = request.user
        booking.save()

        notify_booking_status_updated(booking, old_status)

        messages.success(request, f"✅ Booking #{booking.id} updated successfully. Applicant notified.")
        return redirect('assistance:admin_booking_detail', pk=booking.id)

    context = {
        'booking': booking,
    }
    return render(request, 'assistance/admin_booking_detail.html', context)
