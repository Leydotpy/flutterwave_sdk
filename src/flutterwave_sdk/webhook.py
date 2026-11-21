from __future__ import annotations

import base64
import hashlib
import hmac
import json
from typing import Any, Mapping

from .errors import FlutterwaveError
from .objects import FlutterwaveObject


class WebhookSignatureError(FlutterwaveError):
    """Raised when a webhook signature cannot be verified."""


class Webhook:
    """Webhook verification helpers.

    Flutterwave v4 documentation describes an HMAC-SHA256 signature over the raw body,
    returned in the `flutterwave-signature` header. Older v3 integrations commonly used
    a `verif-hash` header equal to the dashboard secret hash. This helper supports both,
    but defaults to the stronger v4 HMAC mode.
    """

    SIGNATURE_HEADER = "flutterwave-signature"
    LEGACY_SIGNATURE_HEADER = "verif-hash"

    @classmethod
    def verify_signature(
        cls,
        *,
        payload: bytes | str,
        signature: str,
        secret_hash: str,
        digest: str = "base64",
    ) -> bool:
        raw = payload.encode("utf-8") if isinstance(payload, str) else payload
        mac = hmac.new(secret_hash.encode("utf-8"), raw, hashlib.sha256).digest()
        expected = base64.b64encode(mac).decode("ascii") if digest == "base64" else mac.hex()
        return hmac.compare_digest(expected, signature)

    @classmethod
    def verify_legacy_verif_hash(cls, *, signature: str, secret_hash: str) -> bool:
        return hmac.compare_digest(signature, secret_hash)

    @classmethod
    def construct_event(
        cls,
        *,
        payload: bytes | str,
        headers: Mapping[str, str],
        secret_hash: str,
        allow_legacy_verif_hash: bool = False,
    ) -> FlutterwaveObject:
        normalized_headers = {key.lower(): value for key, value in headers.items()}
        signature = normalized_headers.get(cls.SIGNATURE_HEADER)
        legacy_signature = normalized_headers.get(cls.LEGACY_SIGNATURE_HEADER)

        verified = False
        if signature:
            verified = cls.verify_signature(payload=payload, signature=signature, secret_hash=secret_hash)
        elif allow_legacy_verif_hash and legacy_signature:
            verified = cls.verify_legacy_verif_hash(signature=legacy_signature, secret_hash=secret_hash)

        if not verified:
            raise WebhookSignatureError("Invalid Flutterwave webhook signature")

        raw_text = payload.decode("utf-8") if isinstance(payload, bytes) else payload
        try:
            event = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise WebhookSignatureError("Flutterwave webhook payload is not valid JSON") from exc
        return FlutterwaveObject.construct_from(event)
