from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)

class EmailAuthBackend(ModelBackend):
    """
    Email-Only Authentication Backend:
    - Enforces authentication strictly via email address (no usernames allowed).
    - Case-insensitive email lookup (email__iexact).
    - Strips leading and trailing whitespace.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        email = username or kwargs.get('email') or kwargs.get(UserModel.USERNAME_FIELD)

        if not email or not password:
            return None

        clean_email = str(email).strip().lower()

        # Strict email-only lookup
        user = UserModel.objects.filter(email__iexact=clean_email).first()

        if user:
            if user.check_password(password):
                if self.user_can_authenticate(user):
                    return user
                else:
                    logger.warning(f"Authentication failed: Account '{clean_email}' is inactive.")
            else:
                logger.warning(f"Authentication failed: Incorrect password for '{clean_email}'.")
        else:
            logger.warning(f"Authentication failed: No user found for email '{clean_email}'.")

        return None

# Alias for backwards compatibility
EmailOrUsernameModelBackend = EmailAuthBackend
