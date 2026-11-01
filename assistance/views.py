import datetime
import logging
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.db.models import Q
from django.urls import reverse

from .models import AssistancePackage, AssistanceBooking
from .services import (
    ensure_default_packages_seeded,
    notify_booking_created,
    notify_booking_status_updated,
    ServiceOrderService
)
from subscriptions.services import SubscriptionService
from subscriptions.models import PaymentTransaction
from subscriptions.providers import get_payment_provider, PaymentProviderError
from applications.models import Application
from documents.models import Document

logger = logging.getLogger(__name__)


def assistance_home(request):
    """
    Public / Applicant landing page displaying all verified paid assistance packages,
    service categories, delivery times, and pricing in NGN.
    """
    ensure_default_packages_seeded()
    packages = AssistancePackage.objects.filter(is_active=True).order_by('order', 'price')

    category_filter = request.GET.get('category', 'all')
    if category_filter != 'all':
        packages = packages.filter(category=category_filter)

    user_bookings_count = 0
    if request.user.is_authenticated:
        user_bookings_count = AssistanceBooking.objects.filter(user=request.user).count()

    context = {
        'packages': packages,
        'user_bookings_count': user_bookings_count,
        'selected_category': category_filter,
    }
    return render(request, 'assistance/home.html', context)


@login_required
def book_assistance(request, package_slug=None):
    """
    Interactive multi-step service purchasing workflow:
    1. Select service & review price
    2. Link target scholarship / workspace application where applicable
    3. Upload necessary documents or pick from Document Vault
    4. Provide specific notes and preferences
    5. Platform creates ServiceOrder with status 'pending_payment'
    """
    ensure_default_packages_seeded()
    packages = AssistancePackage.objects.filter(is_active=True).order_by('order', 'price')

    selected_package = None
    target_slug = package_slug or request.GET.get('package')
    if target_slug:
        selected_package = packages.filter(slug=target_slug).first()
    if not selected_package:
        selected_package = packages.first()

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
            if package.price_max and package.price_max > base_price:
                final_price = package.price_max
            else:
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
        preferred_contact_method = request.POST.get('preferred_contact_method', 'email')

        # Document attachment
        attached_file = request.FILES.get('attached_document')
        vault_doc_id = request.POST.get('document_vault_ref')
        vault_doc = None
        if vault_doc_id:
            vault_doc = user_documents.filter(id=vault_doc_id).first()

        if not applicant_notes:
            messages.error(request, "Please provide background details and instructions for the reviewer.")
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

        # Redirect user directly to online payment checkout
        return redirect('assistance:service_checkout', pk=booking.id)

    context = {
        'packages': packages,
        'selected_package': selected_package,
        'selected_app_id': selected_app_id,
        'user_applications': user_applications,
        'user_documents': user_documents,
    }
    return render(request, 'assistance/book.html', context)


@login_required
def service_checkout(request, pk):
    """
    Initializes payment for a service order with Paystack or Test Sandbox.
    """
    booking = get_object_or_404(AssistanceBooking, pk=pk, user=request.user)

    if booking.payment_status == 'paid':
        messages.info(request, "This service order has already been paid.")
        return redirect('assistance:booking_detail', pk=booking.id)

    provider = get_payment_provider()
    reference = f"FLII-SRV-{booking.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
    callback_url = request.build_absolute_uri(reverse('assistance:payment_callback', kwargs={'pk': booking.id}))

    # Create PaymentTransaction record
    tx = PaymentTransaction.objects.create(
        user=request.user,
        transaction_type='service_order',
        service_order_id=booking.id,
        reference=reference,
        provider='paystack' if hasattr(provider, 'secret_key') and provider.secret_key else 'test_sandbox',
        amount=booking.price,
        currency=booking.currency,
        status='pending',
        gateway_response={"order_id": booking.id, "package": booking.package_title}
    )

    booking.payment_reference = reference
    booking.payment_transaction = tx
    booking.save(update_fields=['payment_reference', 'payment_transaction', 'updated_at'])

    try:
        init_result = provider.initialize_transaction(
            email=request.user.email,
            amount=booking.price,
            reference=reference,
            callback_url=callback_url,
            metadata={
                "order_id": booking.id,
                "order_number": booking.order_number,
                "service_title": booking.package_title,
                "transaction_type": "service_order",
            },
            currency=booking.currency
        )
        return redirect(init_result["authorization_url"])
    except PaymentProviderError as exc:
        logger.error(f"Failed to initialize service checkout for order #{booking.id}: {exc}")
        messages.error(request, f"Unable to start checkout: {str(exc)}")
        return redirect('assistance:booking_detail', pk=booking.id)


@login_required
def service_payment_callback(request, pk):
    """
    Verifies payment server-side after return from payment gateway.
    """
    booking = get_object_or_404(AssistanceBooking, pk=pk, user=request.user)
    reference = request.GET.get('reference') or request.GET.get('trxref') or booking.payment_reference

    provider = get_payment_provider()
    try:
        verification = provider.verify_transaction(reference)
    except PaymentProviderError as err:
        messages.error(request, f"Verification failed: {str(err)}")
        return redirect('assistance:booking_detail', pk=booking.id)

    if verification.get("is_success"):
        # Update transaction
        if booking.payment_transaction:
            booking.payment_transaction.status = 'success'
            booking.payment_transaction.paid_at = timezone.now()
            booking.payment_transaction.save(update_fields=['status', 'paid_at', 'updated_at'])

        ServiceOrderService.confirm_service_payment(reference)
        messages.success(request, f"🎉 Payment of ₦{booking.price:,.0f} confirmed! Your order is queued for review.")
        return redirect('assistance:booking_detail', pk=booking.id)
    else:
        messages.error(request, "Payment was not successful or was cancelled.")
        return redirect('assistance:booking_detail', pk=booking.id)


@login_required
def my_bookings(request):
    """
    List of all paid assistance service orders for the authenticated applicant.
    """
    filter_status = request.GET.get('status', 'all')
    qs = AssistanceBooking.objects.filter(user=request.user).select_related('package', 'application')

    if filter_status == 'active':
        qs = qs.exclude(status__in=['completed', 'cancelled', 'refunded'])
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
    Applicant order status and deliverables hub.
    Shows current status, reviewer deliverables, meeting links, and additional document upload if requested.
    """
    if request.user.is_staff:
        booking = get_object_or_404(AssistanceBooking.objects.select_related('user', 'package', 'application'), pk=pk)
    else:
        booking = get_object_or_404(AssistanceBooking.objects.select_related('package', 'application'), pk=pk, user=request.user)

    if request.method == 'POST' and request.POST.get('action') == 'upload_additional_docs':
        new_file = request.FILES.get('additional_file')
        if new_file:
            booking.attached_document = new_file
            booking.additional_docs_requested = False
            booking.status = 'in_progress'
            booking.save(update_fields=['attached_document', 'additional_docs_requested', 'status', 'updated_at'])
            messages.success(request, "Additional document uploaded! Reviewer has been notified.")
            return redirect('assistance:booking_detail', pk=booking.id)

    context = {
        'booking': booking,
    }
    return render(request, 'assistance/booking_detail.html', context)


@login_required
def booking_payment_submit(request, pk):
    """
    Fallback manual payment proof submission for bank transfers or offline payments.
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
            "✅ Payment information received! Our team will verify it and begin your review."
        )

    return redirect('assistance:booking_detail', pk=booking.id)


# ==============================================================================
# Reviewer Management & Internal Reviewer Workflow
# Rule: Reviewers have limited permissions. They only access documents and applicant
# information required to fulfil their assigned service orders. Never expose all data.
# ==============================================================================

def is_reviewer_only_user(user):
    """
    Returns True if user is a reviewer with restricted access.
    Superusers and administrators have global visibility.
    Members of the 'Reviewers' group only see orders assigned to them.
    """
    if user.is_superuser:
        return False
    if user.groups.filter(name__iexact='Reviewers').exists():
        return True
    return False


@login_required
def admin_bookings_hub(request):
    """
    Internal Service Orders Hub.
    - Superusers / Admins: Can view all orders, assign reviewers, inspect financials.
    - Reviewers: STRICT DATA ISOLATION. Only sees orders assigned to them.
    """
    if not request.user.is_staff:
        messages.warning(request, "Staff privileges required.")
        return redirect('dashboard:index')

    status_filter = request.GET.get('status', 'all')
    search_q = request.GET.get('q', '').strip()
    reviewer_only = is_reviewer_only_user(request.user)

    # Data Isolation: Reviewers only see assigned orders!
    if reviewer_only:
        qs = AssistanceBooking.objects.filter(assigned_reviewer=request.user).select_related('user', 'package', 'application').order_by('-created_at')
    else:
        qs = AssistanceBooking.objects.select_related('user', 'package', 'application', 'assigned_reviewer').order_by('-created_at')

    if status_filter != 'all':
        qs = qs.filter(status=status_filter)

    if search_q:
        qs = qs.filter(
            Q(order_number__icontains=search_q) |
            Q(user__email__icontains=search_q) |
            Q(user__first_name__icontains=search_q) |
            Q(package_title__icontains=search_q)
        )

    from django.contrib.auth import get_user_model
    User = get_user_model()
    available_reviewers = User.objects.filter(is_staff=True).order_by('first_name')

    context = {
        'bookings': qs,
        'current_status': status_filter,
        'search_q': search_q,
        'total_count': qs.count(),
        'is_reviewer_only': reviewer_only,
        'available_reviewers': available_reviewers,
    }
    return render(request, 'assistance/admin_hub.html', context)


@login_required
def admin_booking_detail(request, pk):
    """
    Workbench for reviewing and fulfilling a single assigned service order.
    Strict Data Isolation: A reviewer can only view their own assigned orders.
    """
    if not request.user.is_staff:
        return HttpResponseForbidden("Unauthorized")

    reviewer_only = is_reviewer_only_user(request.user)
    if reviewer_only:
        # Non-superusers with reviewer role can only access their assigned orders!
        booking = get_object_or_404(AssistanceBooking.objects.select_related('user', 'package', 'application'), pk=pk, assigned_reviewer=request.user)
    else:
        booking = get_object_or_404(AssistanceBooking.objects.select_related('user', 'package', 'application', 'assigned_reviewer'), pk=pk)

    from django.contrib.auth import get_user_model
    User = get_user_model()
    available_reviewers = User.objects.filter(is_staff=True).order_by('first_name')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'assign_reviewer' and not reviewer_only:
            reviewer_id = request.POST.get('reviewer_id')
            reviewer = get_object_or_404(User, id=reviewer_id, is_staff=True)
            ServiceOrderService.assign_reviewer(booking, reviewer, admin_user=request.user)
            messages.success(request, f"Assigned to {reviewer.get_full_name() or reviewer.email}.")
            return redirect('assistance:admin_booking_detail', pk=booking.id)

        elif action == 'request_documents':
            doc_notes = request.POST.get('additional_docs_notes', '').strip()
            booking.additional_docs_requested = True
            booking.additional_docs_notes = doc_notes
            booking.status = 'awaiting_user_info'
            booking.save(update_fields=['additional_docs_requested', 'additional_docs_notes', 'status', 'updated_at'])

            from notifications.models import Notification
            Notification.objects.create(
                user=booking.user,
                title=f"⚠️ Additional Document Required: #{booking.order_number}",
                message=f"Reviewer notes: {doc_notes}",
                notification_type='system'
            )
            messages.success(request, "Applicant notified to provide requested additional documents.")
            return redirect('assistance:admin_booking_detail', pk=booking.id)

        elif action == 'submit_deliverable':
            feedback = request.POST.get('deliverable_feedback', '').strip()
            deliverable_file = request.FILES.get('deliverable_file')
            mark_complete = request.POST.get('mark_complete') == '1'

            if mark_complete:
                ServiceOrderService.complete_order(booking, feedback, deliverable_file)
                messages.success(request, f"🎉 Order #{booking.order_number} marked as completed and deliverable dispatched to applicant.")
            else:
                booking.deliverable_feedback = feedback
                if deliverable_file:
                    booking.deliverable_file = deliverable_file
                booking.status = 'ready_for_review'
                booking.save()
                messages.success(request, "Draft feedback saved.")
            return redirect('assistance:admin_booking_detail', pk=booking.id)

        else:
            # Handles general updates, status changes, live call scheduling, and payment updates
            old_status = booking.status
            new_status = request.POST.get('status', booking.status)
            booking.status = new_status

            payment_status = request.POST.get('payment_status')
            if payment_status:
                booking.payment_status = payment_status

            meeting_link = request.POST.get('meeting_link', '').strip()
            if meeting_link:
                booking.meeting_link = meeting_link

            scheduled_at = request.POST.get('scheduled_at')
            if scheduled_at:
                try:
                    booking.scheduled_at = timezone.datetime.fromisoformat(scheduled_at)
                except (ValueError, TypeError):
                    pass

            deliverable_feedback = request.POST.get('deliverable_feedback', '').strip()
            if deliverable_feedback:
                booking.deliverable_feedback = deliverable_feedback

            deliverable_file = request.FILES.get('deliverable_file')
            if deliverable_file:
                booking.deliverable_file = deliverable_file

            admin_notes = request.POST.get('admin_notes', '').strip()
            if admin_notes:
                booking.admin_notes = admin_notes

            booking.assigned_admin = request.user
            booking.save()

            if new_status == 'scheduled' and booking.meeting_link:
                from notifications.models import Notification
                Notification.objects.create(
                    user=booking.user,
                    title=f"🗓️ Live Session Scheduled: {booking.package_title}",
                    message=f"Your session is set for {booking.scheduled_at}. Link: {booking.meeting_link}",
                    notification_type='system'
                )

            notify_booking_status_updated(booking, old_status)
            messages.success(request, f"Order #{booking.order_number} updated.")
            return redirect('assistance:admin_booking_detail', pk=booking.id)

    context = {
        'booking': booking,
        'available_reviewers': available_reviewers,
        'is_reviewer_only': reviewer_only,
    }
    return render(request, 'assistance/admin_booking_detail.html', context)

