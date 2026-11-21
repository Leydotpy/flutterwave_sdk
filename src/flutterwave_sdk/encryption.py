from __future__ import annotations

import base64
import secrets
import string
from dataclasses import dataclass
from typing import Mapping

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


_NONCE_ALPHABET = string.ascii_letters + string.digits


class EncryptionError(ValueError):
    """Raised when Flutterwave card encryption input is invalid."""


@dataclass(frozen=True, slots=True)
class EncryptedValue:
    """Single encrypted value plus the nonce used to produce it."""

    encrypted: str
    nonce: str


def generate_nonce(length: int = 12) -> str:
    """Generate a Flutterwave-compatible AES-GCM nonce.

    Flutterwave's card documentation uses a 12-character nonce. Keep the default unless
    the API explicitly changes its requirement.
    """

    if length != 12:
        raise EncryptionError("Flutterwave AES-GCM card encryption requires a 12-character nonce.")
    return "".join(secrets.choice(_NONCE_ALPHABET) for _ in range(length))


def decode_encryption_key(encryption_key: str) -> bytes:
    """Decode and validate a base64 Flutterwave encryption key."""

    if not encryption_key:
        raise EncryptionError("encryption_key is required.")
    try:
        key = base64.b64decode(encryption_key, validate=True)
    except Exception as exc:  # pragma: no cover - exact exception varies by Python version
        raise EncryptionError("encryption_key must be base64 encoded.") from exc
    if len(key) != 32:
        raise EncryptionError(
            "Flutterwave card encryption uses AES-256, so the decoded encryption key must be 32 bytes."
        )
    return key


def encrypt_aes_gcm(plain_text: str, *, encryption_key: str, nonce: str | None = None) -> EncryptedValue:
    """Encrypt a string using Flutterwave's AES-256-GCM card-encryption convention.

    The return value is base64 encoded and includes the authentication tag, matching the
    WebCrypto/Java/Python examples in Flutterwave's encryption docs.
    """

    if plain_text is None or str(plain_text) == "":
        raise EncryptionError("plain_text must not be empty.")
    nonce_to_use = nonce or generate_nonce()
    if len(nonce_to_use) != 12:
        raise EncryptionError("nonce must be exactly 12 characters long.")

    key = decode_encryption_key(encryption_key)
    aes_gcm = AESGCM(key)
    encrypted = aes_gcm.encrypt(nonce_to_use.encode("utf-8"), str(plain_text).encode("utf-8"), None)
    return EncryptedValue(encrypted=base64.b64encode(encrypted).decode("ascii"), nonce=nonce_to_use)


def encrypt_card_details(
    *,
    card_number: str,
    expiry_month: str | int,
    expiry_year: str | int,
    cvv: str,
    encryption_key: str,
    nonce: str | None = None,
) -> dict[str, str]:
    """Return a Flutterwave `card` payload with encrypted card fields.

    Do not persist the raw arguments passed to this function. The returned dictionary is
    safe to pass directly as the `card=` parameter to `client.payment_methods.create(...)`.
    """

    nonce_to_use = nonce or generate_nonce()
    normalized_card_number = "".join(str(card_number).split())
    normalized_month = str(expiry_month).zfill(2)
    normalized_year = str(expiry_year)
    normalized_cvv = str(cvv).strip()

    return {
        "nonce": nonce_to_use,
        "encrypted_card_number": encrypt_aes_gcm(
            normalized_card_number, encryption_key=encryption_key, nonce=nonce_to_use
        ).encrypted,
        "encrypted_expiry_month": encrypt_aes_gcm(
            normalized_month, encryption_key=encryption_key, nonce=nonce_to_use
        ).encrypted,
        "encrypted_expiry_year": encrypt_aes_gcm(
            normalized_year, encryption_key=encryption_key, nonce=nonce_to_use
        ).encrypted,
        "encrypted_cvv": encrypt_aes_gcm(
            normalized_cvv, encryption_key=encryption_key, nonce=nonce_to_use
        ).encrypted,
    }


def encrypt_pin(*, pin: str, encryption_key: str, nonce: str | None = None) -> dict[str, str]:
    """Return a Flutterwave authorization PIN payload."""

    encrypted = encrypt_aes_gcm(str(pin).strip(), encryption_key=encryption_key, nonce=nonce)
    return {"nonce": encrypted.nonce, "encrypted_pin": encrypted.encrypted}


def encrypt_dict_fields(
    data: Mapping[str, object],
    *,
    encryption_key: str,
    nonce: str | None = None,
) -> dict[str, str]:
    """Encrypt arbitrary fields with a shared nonce.

    This is useful for future Flutterwave encrypted-field flows while keeping card-specific
    helpers ergonomic.
    """

    nonce_to_use = nonce or generate_nonce()
    encrypted: dict[str, str] = {"nonce": nonce_to_use}
    for key, value in data.items():
        encrypted[key] = encrypt_aes_gcm(str(value), encryption_key=encryption_key, nonce=nonce_to_use).encrypted
    return encrypted
