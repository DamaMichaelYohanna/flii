import hmac
import hashlib
import json
import logging
import requests
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from decimal import Decimal
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

logger = logging.getLogger(__name__)


class PaymentProviderError(Exception):
    """Custom exception raised during payment processing."""
    pass


class BasePaymentProvider(ABC):
    """
    Abstract interface for payment gateway providers.
    Ensures provider-agnostic architecture.
    """

    @abstractmethod
    def initialize_transaction(
        self,
        email: str,
        amount: Decimal,
        reference: str,
        callback_url: str,
        metadata: Optional[Dict[str, Any]] = None,
        currency: str = 'NGN'
    ) -> Dict[str, Any]:
        """
        Initializes a transaction with the payment gateway.
        Returns:
            Dict containing 'authorization_url', 'reference', 'access_code'
        """
        pass

    @abstractmethod
    def verify_transaction(self, reference: str) -> Dict[str, Any]:
        """
        Verifies transaction status directly with gateway API server-side.
        Returns:
            Dict containing 'status' (success/failed), 'amount', 'currency', 'reference', 'raw_response'
        """
        pass

    @abstractmethod
    def verify_webhook_signature(self, payload_bytes: bytes, signature_header: str) -> bool:
        """
        Validates cryptographic webhook signature to ensure authenticity.
        """
        pass


class PaystackPaymentProvider(BasePaymentProvider):
    """
    Paystack Payment Gateway Provider for Nigerian and African users.
    Implements REST endpoints and HMAC-SHA512 webhook signature verification.
    """
    BASE_URL = "https://api.paystack.co"

    def __init__(self, secret_key: Optional[str] = None, public_key: Optional[str] = None):
        self.secret_key = secret_key or getattr(settings, 'PAYSTACK_SECRET_KEY', '')
        self.public_key = public_key or getattr(settings, 'PAYSTACK_PUBLIC_KEY', '')

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def initialize_transaction(
        self,
        email: str,
        amount: Decimal,
        reference: str,
        callback_url: str,
        metadata: Optional[Dict[str, Any]] = None,
        currency: str = 'NGN'
    ) -> Dict[str, Any]:
        """
        Calls Paystack /transaction/initialize
        Amounts in Paystack must be in the lowest currency subunit (kobo for NGN: 1 NGN = 100 kobo).
        """
        if not self.secret_key:
            raise PaymentProviderError("Paystack secret key is not configured in settings.")

        # Convert Naira to Kobo
        amount_in_kobo = int(amount * 100)

        payload = {
            "email": email,
            "amount": amount_in_kobo,
            "reference": reference,
            "callback_url": callback_url,
            "currency": currency,
            "metadata": metadata or {},
        }

        try:
            url = f"{self.BASE_URL}/transaction/initialize"
            response = requests.post(url, headers=self._get_headers(), json=payload, timeout=15)
            data = response.json()

            if response.status_code == 200 and data.get("status") is True:
                resp_data = data.get("data", {})
                return {
                    "authorization_url": resp_data.get("authorization_url"),
                    "access_code": resp_data.get("access_code"),
                    "reference": resp_data.get("reference", reference),
                    "raw_response": data,
                }
            else:
                msg = data.get("message", "Paystack initialization failed.")
                logger.error(f"Paystack init failed: {msg}")
                raise PaymentProviderError(msg)
        except requests.RequestException as exc:
            logger.exception("Network error while connecting to Paystack.")
            raise PaymentProviderError(f"Connection to Paystack gateway failed: {str(exc)}")

    def verify_transaction(self, reference: str) -> Dict[str, Any]:
        """
        Calls Paystack /transaction/verify/:reference server-side.
        """
        if not self.secret_key:
            raise PaymentProviderError("Paystack secret key is not configured in settings.")

        try:
            url = f"{self.BASE_URL}/transaction/verify/{reference}"
            response = requests.get(url, headers=self._get_headers(), timeout=15)
            data = response.json()

            if response.status_code == 200 and data.get("status") is True:
                transaction_data = data.get("data", {})
                is_success = transaction_data.get("status") == "success"
                # Convert kobo back to standard Naira
                amount_paid = Decimal(str(transaction_data.get("amount", 0))) / Decimal('100')

                return {
                    "is_success": is_success,
                    "status": "success" if is_success else transaction_data.get("status", "failed"),
                    "amount": amount_paid,
                    "currency": transaction_data.get("currency", "NGN"),
                    "reference": transaction_data.get("reference", reference),
                    "channel": transaction_data.get("channel", "card"),
                    "paid_at": transaction_data.get("paid_at"),
                    "gateway_response": transaction_data.get("gateway_response", ""),
                    "raw_response": transaction_data,
                }
            else:
                msg = data.get("message", "Transaction verification failed.")
                return {
                    "is_success": False,
                    "status": "failed",
                    "reference": reference,
                    "gateway_response": msg,
                    "raw_response": data,
                }
        except requests.RequestException as exc:
            logger.exception(f"Verification request failed for reference {reference}")
            raise PaymentProviderError(f"Unable to verify transaction with Paystack: {str(exc)}")

    def verify_webhook_signature(self, payload_bytes: bytes, signature_header: str) -> bool:
        """
        Paystack sends the HMAC SHA512 signature in the 'x-paystack-signature' header.
        """
        if not self.secret_key or not signature_header:
            return False

        computed_signature = hmac.new(
            key=self.secret_key.encode('utf-8'),
            msg=payload_bytes,
            digestmod=hashlib.sha512
        ).hexdigest()

        return hmac.compare_digest(computed_signature, signature_header)


class MockSandboxPaymentProvider(BasePaymentProvider):
    """
    Test Mode / Sandbox Payment Provider.
    Activated when live Paystack credentials are not configured or in development/test mode.
    Provides a seamless checkout experience with realistic verification simulation.
    """

    def initialize_transaction(
        self,
        email: str,
        amount: Decimal,
        reference: str,
        callback_url: str,
        metadata: Optional[Dict[str, Any]] = None,
        currency: str = 'NGN'
    ) -> Dict[str, Any]:
        """
        Generates internal sandbox URL.
        """
        sandbox_url = reverse('subscriptions:sandbox_checkout', kwargs={'reference': reference})
        return {
            "authorization_url": sandbox_url,
            "access_code": f"MOCK_{reference[:8]}",
            "reference": reference,
            "raw_response": {"mode": "test_sandbox", "amount": float(amount)},
        }

    def verify_transaction(self, reference: str) -> Dict[str, Any]:
        """
        Simulates instant successful verification for test sandbox transactions.
        """
        from .models import PaymentTransaction
        tx = PaymentTransaction.objects.filter(reference=reference).first()
        amount = tx.amount if tx else Decimal('3000.00')

        return {
            "is_success": True,
            "status": "success",
            "amount": amount,
            "currency": "NGN",
            "reference": reference,
            "channel": "test_sandbox_card",
            "paid_at": timezone.now().isoformat(),
            "gateway_response": "Successful test transaction (Flii Sandbox)",
            "raw_response": {"simulated": True},
        }

    def verify_webhook_signature(self, payload_bytes: bytes, signature_header: str) -> bool:
        """
        In sandbox mode, validates test signature header or fallback token.
        """
        return signature_header == "test_sandbox_valid_sig" or getattr(settings, 'DEBUG', False)


def get_payment_provider() -> BasePaymentProvider:
    """
    Factory function returning the configured payment provider.
    Defaults to Paystack if PAYSTACK_SECRET_KEY is present and not explicitly in mock mode.
    Falls back gracefully to MockSandboxPaymentProvider if credentials are not configured.
    """
    secret = getattr(settings, 'PAYSTACK_SECRET_KEY', '').strip()
    force_mock = getattr(settings, 'PAYSTACK_MOCK_MODE', False)

    if secret and not force_mock:
        return PaystackPaymentProvider(secret_key=secret)
    return MockSandboxPaymentProvider()
