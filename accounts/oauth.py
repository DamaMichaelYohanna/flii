import os
import secrets
import logging
import requests
from urllib.parse import urlencode
from typing import Dict, Any, Optional, Tuple
from django.conf import settings
from django.contrib.auth import get_user_model
from applicants.models import ApplicantProfile

logger = logging.getLogger(__name__)
User = get_user_model()

class GoogleOAuthService:
    """
    Handles Google OAuth2 / OpenID Connect authentication flow.
    Supports standard Google API token exchange, user info fetching, and user provisioning.
    """
    AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
    USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v3/userinfo"

    def __init__(self):
        self.client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '') or os.environ.get('GOOGLE_CLIENT_ID', '')
        self.client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', '') or os.environ.get('GOOGLE_CLIENT_SECRET', '')

    @property
    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def get_authorization_url(self, request, redirect_uri: str) -> str:
        """
        Generates authorization URL with CSRF protection state parameter.
        """
        state = secrets.token_urlsafe(32)
        request.session['google_oauth_state'] = state

        params = {
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'openid email profile',
            'access_type': 'online',
            'state': state,
            'prompt': 'select_account',
        }
        return f"{self.AUTH_ENDPOINT}?{urlencode(params)}"

    def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> Optional[Dict[str, Any]]:
        """
        Exchanges authorization code for access and ID tokens.
        """
        data = {
            'code': code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
        }
        try:
            resp = requests.post(self.TOKEN_ENDPOINT, data=data, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            logger.error(f"Google token exchange failed: {resp.status_code} {resp.text}")
        except Exception as e:
            logger.error(f"Exception during Google token exchange: {e}")
        return None

    def fetch_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Fetches user profile information using access token.
        """
        headers = {'Authorization': f'Bearer {access_token}'}
        try:
            resp = requests.get(self.USERINFO_ENDPOINT, headers=headers, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            logger.error(f"Google userinfo request failed: {resp.status_code} {resp.text}")
        except Exception as e:
            logger.error(f"Exception fetching Google userinfo: {e}")
        return None

    def get_or_create_user(self, google_info: Dict[str, Any]) -> Tuple[User, bool]:
        """
        Finds existing user by email or provisions a new verified user and applicant profile.
        """
        email = google_info.get('email', '').strip().lower()
        if not email:
            raise ValueError("Google profile did not contain an email address.")

        first_name = google_info.get('given_name', '')
        last_name = google_info.get('family_name', '')
        
        user = User.objects.filter(email__iexact=email).first()
        created = False

        if not user:
            # Generate unique username
            base_username = email.split('@')[0]
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1

            user = User.objects.create(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_email_verified=True
            )
            user.set_unusable_password()
            user.save()
            created = True

            # Initialize profile
            ApplicantProfile.objects.create(
                user=user,
                country_of_origin='Nigeria',
                nationality='Nigerian'
            )
        else:
            # Update verification status & names if empty
            if not user.is_email_verified:
                user.is_email_verified = True
            if not user.first_name and first_name:
                user.first_name = first_name
            if not user.last_name and last_name:
                user.last_name = last_name
            user.save()

            # Ensure profile exists
            ApplicantProfile.objects.get_or_create(
                user=user,
                defaults={'country_of_origin': 'Nigeria', 'nationality': 'Nigerian'}
            )

        return user, created
