import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone

from .models import SubscriptionPlan, Subscription, PaymentTransaction
from .services import SubscriptionService
from .entitlements import EntitlementService
from .providers import PaymentProviderError

logger = logging.getLogger(__name__)


def pricing_plans_view(request):
    """
    Renders the subscription pricing comparison page.
    Monthly: ₦3,000 | Three-Month: ₦7,500 | Annual: ₦20,000 | Free: ₦0
    """
    SubscriptionService.seed_default_plans_and_features()
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('order', 'price')

    active_sub = None
    current_plan_code = 'free'
    if request.user.is_authenticated:
        active_sub = EntitlementService.get_active_subscription(request.user)
        if active_sub:
            current_plan_code = active_sub.plan.plan_code

    context = {
        'plans': plans,
        'active_sub': active_sub,
        'current_plan_code': current_plan_code,
    }
    return render(request, 'subscriptions/pricing.html', context)


@login_required
def checkout_initialize_view(request, plan_id):
    """
    Initializes server-side payment transaction with Paystack (or sandbox mode).
    Never trusts client input for amount or parameters.
    """
    plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)

    if plan.is_free:
        messages.info(request, "You are already on the Free tier.")
        return redirect('opportunities:list')

    callback_url = request.build_absolute_uri(reverse('subscriptions:callback'))

    try:
        checkout_data = SubscriptionService.initialize_subscription_checkout(
            user=request.user,
            plan_id=plan.id,
            callback_url=callback_url
        )
        return redirect(checkout_data["authorization_url"])
    except (ValueError, PaymentProviderError) as exc:
        logger.error(f"Failed to initialize checkout for user {request.user.email}: {exc}")
        messages.error(request, f"Unable to start checkout: {str(exc)}")
        return redirect('subscriptions:pricing')


@login_required
def paystack_callback_view(request):
    """
    Redirect endpoint called by Paystack after user interaction.
    Crucial Rule: Do NOT activate subscription based solely on redirect.
    Always verify server-side with Paystack before activating.
    """
    reference = request.GET.get('reference') or request.GET.get('trxref')
    if not reference:
        messages.error(request, "No payment reference provided in callback.")
        return redirect('subscriptions:pricing')

    success, message, sub = SubscriptionService.verify_and_activate_subscription(reference)
    if success:
        messages.success(request, f"🎉 {message}")
        return redirect('subscriptions:manage')
    else:
        messages.error(request, f"Payment failed: {message}")
        return redirect('subscriptions:pricing')


@csrf_exempt
def paystack_webhook_view(request):
    """
    Asynchronous webhook receiver for Paystack payment notifications.
    Features:
    - HMAC SHA512 signature validation
    - Idempotent processing
    - Prevents double-crediting
    """
    if request.method != 'POST':
        return HttpResponseBadRequest("Method not allowed")

    signature_header = request.headers.get('x-paystack-signature', '')
    raw_body = request.body

    try:
        payload = json.loads(raw_body.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return HttpResponseBadRequest("Invalid JSON body")

    success, message, status_code = SubscriptionService.handle_paystack_webhook(
        payload=payload,
        raw_body=raw_body,
        signature_header=signature_header
    )

    return JsonResponse({"status": "success" if success else "error", "message": message}, status=status_code)


def test_sandbox_checkout_view(request, reference):
    """
    Interactive Test Mode Sandbox Checkout UI.
    Provides a safe, realistic payment simulation interface when live gateway keys are absent.
    """
    tx = get_object_or_404(PaymentTransaction, reference=reference)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'simulate_success':
            success, msg, sub = SubscriptionService.verify_and_activate_subscription(reference)
            if success:
                messages.success(request, f"✅ Test payment successful! Your subscription is now active.")
                return redirect('subscriptions:manage')
            else:
                messages.error(request, f"Simulation error: {msg}")
                return redirect('subscriptions:pricing')
        elif action == 'simulate_failure':
            tx.status = 'failed'
            tx.gateway_response = {"simulated": "declined", "reason": "Insufficient test funds"}
            tx.save()
            messages.error(request, "❌ Test payment was declined as simulated.")
            return redirect('subscriptions:pricing')

    context = {
        'transaction': tx,
        'reference': reference,
    }
    return render(request, 'subscriptions/sandbox_checkout.html', context)


@login_required
def manage_subscription_view(request):
    """
    Applicant subscription management portal.
    Shows current status, renewal date, payment history, and cancellation options.
    """
    SubscriptionService.seed_default_plans_and_features()
    active_sub = EntitlementService.get_active_subscription(request.user)
    entitlements = EntitlementService.get_entitlements_summary(request.user)
    transactions = PaymentTransaction.objects.filter(user=request.user).order_by('-created_at')[:15]

    context = {
        'subscription': active_sub,
        'entitlements': entitlements,
        'transactions': transactions,
    }
    return render(request, 'subscriptions/manage.html', context)


@login_required
def cancel_subscription_view(request):
    """
    Cancels the user's active premium subscription with user feedback.
    """
    if request.method == 'POST':
        reason = request.POST.get('cancellation_reason', '').strip()
        success, message = SubscriptionService.cancel_subscription(request.user, reason=reason)
        if success:
            messages.success(request, message)
        else:
            messages.warning(request, message)
        return redirect('subscriptions:manage')

    return redirect('subscriptions:manage')
