from .entitlements import EntitlementService

def subscription_context(request):
    """
    Context processor injecting user's subscription and entitlement state.
    """
    if not request.user.is_authenticated:
        return {
            'is_premium': False,
            'user_subscription': None,
            'user_entitlements': None,
        }

    sub = EntitlementService.get_active_subscription(request.user)
    is_premium = sub.is_premium if sub else False

    return {
        'is_premium': is_premium,
        'user_subscription': sub,
        'user_entitlements': EntitlementService.get_entitlements_summary(request.user),
    }
