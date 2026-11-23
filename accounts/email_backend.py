import logging

import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import EmailMessage

logger = logging.getLogger(__name__)


class ResendEmailBackend(BaseEmailBackend):
    """Send Django email messages through the Resend HTTP API."""

    api_url = "https://api.resend.com/emails"

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        api_key = getattr(settings, "RESEND_API_KEY", "")
        if not api_key:
            if self.fail_silently:
                return 0
            raise RuntimeError("RESEND_API_KEY is required for the Resend email backend")

        sent = 0
        for message in email_messages:
            if not isinstance(message, EmailMessage) or not message.recipients():
                continue

            payload = {
                "from": message.from_email,
                "to": message.recipients(),
                "subject": message.subject,
                "text": message.body,
            }
            for content, mimetype in message.alternatives:
                if mimetype == "text/html":
                    payload["html"] = content
                    break

            try:
                response = requests.post(
                    self.api_url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=getattr(settings, "EMAIL_TIMEOUT", 10),
                )
                response.raise_for_status()
            except requests.RequestException:
                logger.exception("Resend failed to send email to %s", message.recipients())
                if not self.fail_silently:
                    raise
                continue

            sent += 1

        return sent
