import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
import os

logger = logging.getLogger(__name__)

def get_base_url(request=None):
    """
    Computes protocol and domain safely from request or settings.
    """
    if request is not None:
        protocol = 'https' if (request.is_secure() or not getattr(settings, 'DEBUG', False)) else 'http'
        domain = request.get_host()
    else:
        protocol = 'https' if not getattr(settings, 'DEBUG', False) else 'http'
        domain = os.environ.get('APP_DOMAIN', 'leapatlas.org')
    return protocol, domain

def send_verification_email(request, user):
    """
    Generates a secure email verification token and sends a branded
    multipart (HTML + Plaintext fallback) confirmation email to the user.
    """
    if not user or not user.email:
        return False

    try:
        protocol, domain = get_base_url(request)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        verify_url = f"{protocol}://{domain}/verify-email/{uidb64}/{token}/"

        subject = "Confirm your email address - LeapAtlas Workspace"
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'LeapAtlas Support <support@leapatlas.org>')
        to_email = user.email

        context = {
            'user': user,
            'email': user.email,
            'verify_url': verify_url,
            'protocol': protocol,
            'domain': domain,
            'first_name': user.first_name or user.username,
        }

        html_content = render_to_string('accounts/emails/verify_email.html', context)
        text_content = render_to_string('accounts/emails/verify_email.txt', context)

        msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)

        if getattr(settings, 'DEBUG', False):
            print("\n" + "=" * 70)
            print(f"  [LEAPATLAS DEV EMAIL] VERIFICATION LINK SENT TO: {to_email}")
            print(f"  CLICKABLE VERIFICATION URL:")
            print(f"  --> {verify_url}")
            print("=" * 70 + "\n")

        return True

    except Exception as e:
        logger.error(f"Failed to dispatch email verification message to {getattr(user, 'email', 'unknown')}: {e}", exc_info=True)
        if getattr(settings, 'DEBUG', False):
            print(f"  [LEAPATLAS DEV EMAIL ERROR] Could not dispatch verification email: {e}")
        return False
