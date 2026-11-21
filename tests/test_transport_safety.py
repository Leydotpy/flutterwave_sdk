import base64
import hashlib
import hmac
from decimal import Decimal

import httpx
import pytest

from flutterwave_sdk import FlutterwaveClient, RequestOptions, Webhook
from flutterwave_sdk.errors import APIError, InvalidRequestOptionsError
from flutterwave_sdk.webhook import WebhookSignatureError


def test_non_idempotent_post_is_not_retried():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(503, json={"message": "unavailable"})

    transport = httpx.Client(transport=httpx.MockTransport(handler))
    with FlutterwaveClient(access_token="test", http_client=transport, max_network_retries=3) as client:
        with pytest.raises(APIError):
            client.request_raw("POST", "/charges", json={"amount": "1"})
    assert len(calls) == 1


def test_idempotent_post_can_be_retried():
    calls = []

    def handler(request):
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(503, json={"message": "temporary"})
        return httpx.Response(200, json={"status": "success", "data": {"id": "ok"}})

    transport = httpx.Client(transport=httpx.MockTransport(handler))
    with FlutterwaveClient(access_token="test", http_client=transport, max_network_retries=2) as client:
        result = client.request_raw(
            "POST", "/charges", json={"amount": "1"},
            options=RequestOptions(idempotency_key="a" * 32),
        )
    assert result.data.id == "ok"
    assert len(calls) == 2


def test_idempotency_key_format():
    with pytest.raises(InvalidRequestOptionsError):
        RequestOptions(idempotency_key="payment-intent-1234567").to_headers()


def test_v4_signature_with_explicit_legacy_opt_in():
    payload = b'{"type":"charge.completed"}'
    secret = "secret"
    digest = hmac.new(secret.encode(), payload, hashlib.sha256).digest()
    signature = base64.b64encode(digest).decode()
    event = Webhook.construct_event(
        payload=payload, headers={"flutterwave-signature": signature}, secret_hash=secret
    )
    assert event.type == "charge.completed"
    with pytest.raises(WebhookSignatureError):
        Webhook.construct_event(payload=payload, headers={"verif-hash": secret}, secret_hash=secret)


def test_decimal_amount_serializes_as_exact_json_number():
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(201, json={"status": "success", "data": {"id": "one"}})

    transport = httpx.Client(transport=httpx.MockTransport(handler))
    with FlutterwaveClient(access_token="test", http_client=transport) as client:
        client.request_raw(
            "POST", "/charges", json={"amount": Decimal("123456789.01")},
            options=RequestOptions(idempotency_key="b" * 32),
        )
    assert b'123456789.01' in requests[0].content
    assert b'123456789.009999' not in requests[0].content
