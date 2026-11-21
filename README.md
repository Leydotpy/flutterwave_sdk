# Flutterwave SDK for Python

A Python client for the **Flutterwave v4 API**, built around explicit service objects, OAuth 2.0 client-credentials authentication, structured responses, typed request parameters, and reusable payment workflows.

> **Project status:** Early development (version **0.1.0**). This is an independent, **unofficial** Python SDK and is not represented as an officially maintained Flutterwave package. Review the [installation status](#installation), [security considerations](#security-considerations), and [current limitations](#current-limitations) before using it with real payments.

## Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration and authentication](#configuration-and-authentication)
- [Quick start](#quick-start)
- [Service reference](#service-reference)
- [Common workflows](#common-workflows)
- [Card payments and encryption](#card-payments-and-encryption)
- [Transaction verification](#transaction-verification)
- [Webhooks](#webhooks)
- [Request options and idempotency](#request-options-and-idempotency)
- [Responses and pagination](#responses-and-pagination)
- [Error handling](#error-handling)
- [Custom requests and environments](#custom-requests-and-environments)
- [Security considerations](#security-considerations)
- [Project structure](#project-structure)
- [Current limitations](#current-limitations)
- [Development and contributing](#development-and-contributing)
- [Further reading](#further-reading)

## Features

The current source tree provides:

- **Instance-based client configuration:** independent sandbox and production clients without global API credentials.
- **Flutterwave v4 service objects:** customers, payment methods, charges, orchestration, banks, mobile networks, virtual accounts, transfers, wallets, refunds, settlements, orders, chargebacks, fees, and transaction verification.
- **OAuth 2.0 authentication:** client-credentials token acquisition, in-memory token caching, and refresh on expiry; or an explicitly supplied access token.
- **Synchronous HTTP transport:** powered by `httpx`, with configurable timeout, injected HTTP client, network retries, and API error mapping.
- **Structured return values:** `FlutterwaveResponse`, attribute-accessible `FlutterwaveObject`, and `ListObject` pagination helpers.
- **Card workflow helpers:** encrypted card payload creation, customer → payment method → charge orchestration, direct charges, and PIN/OTP follow-up methods.
- **Webhook helpers:** HMAC-SHA256 signature verification and optional legacy `verif-hash` support.
- **Per-request metadata:** idempotency, trace, and scenario headers via `RequestOptions`.
- **Typed request definitions:** `TypedDict` and literal types for selected request payloads; a `py.typed` marker is present.
- **Escape hatch:** `request_raw()` for endpoints not wrapped by a dedicated service.

The SDK wraps HTTP operations; it does **not** run a payment server, host a checkout UI, persist transaction state, or guarantee that every endpoint is enabled for every Flutterwave account.

## Requirements

- **Python 3.14 or later**, as declared in `pyproject.toml` and `.python-version`.
- `httpx>=0.28.1`.
- `cryptography>=47.0.0`.
- Flutterwave v4 credentials for your chosen environment, or an existing OAuth access token.
- An encryption key for the card-encryption helpers.

Version declared in the repository: `0.1.0`.

## Installation

### Run from a source checkout (current supported approach)

~~~bash
git clone https://github.com/Leydotpy/flutterwave_sdk.git
cd flutterwave_sdk

# Install uv first if it is not already available:
# https://docs.astral.sh/uv/getting-started/installation/
uv sync
~~~

**Important packaging note:** The repository currently keeps its Python package files at the repository root and does not declare a `[build-system]` in `pyproject.toml`. `uv sync` prepares the project environment and dependencies; it does **not** establish that `flutterwave_sdk` has been built and installed as a distributable package. Do not assume `pip install flutterwave-sdk` installs this repository's code or that a PyPI release exists.

Until packaging is added, execute your application with the **parent directory of the checkout** on Python's import path. One way to verify a source checkout, starting in the repository directory, is:

~~~bash
cd ..
./flutterwave_sdk/.venv/bin/python -c "from flutterwave_sdk import FlutterwaveClient; print('SDK import OK')"
~~~

On Windows PowerShell, the equivalent executable is `.\flutterwave_sdk\.venv\Scripts\python.exe`.

For another project, make the checkout's **parent directory** importable (for example via your development environment's `PYTHONPATH`), and use a Python environment containing the dependencies above. A conventional editable-install workflow should be documented only after the project gains packaging configuration.

## Configuration and authentication

The client accepts the following keyword-only arguments:

| Option | Default | Purpose |
| --- | --- | --- |
| `client_id` | `None` | Flutterwave OAuth client ID |
| `client_secret` | `None` | Flutterwave OAuth client secret |
| `access_token` | `None` | Existing bearer access token, if you are managing it yourself |
| `environment` | `"sandbox"` | `"sandbox"` or `"production"`, or a custom `Environment` |
| `http_client` | `None` | Optional preconfigured synchronous `httpx.Client` |
| `timeout` | `30.0` | Timeout in seconds for an internally created HTTP client |
| `max_network_retries` | `2` | Additional retry attempts after the first request |
| `token_url` | Flutterwave identity-provider URL | Override the OAuth token endpoint |
| `encryption_key` | `None` | Base64-encoded card encryption key for convenience helpers |

### Environment variables

A suggested application-side convention is:

~~~bash
export FLW_CLIENT_ID="your-client-id"
export FLW_CLIENT_SECRET="your-client-secret"
export FLW_ENCRYPTION_KEY="your-base64-encryption-key"
export FLW_WEBHOOK_SECRET="your-webhook-secret"
export FLW_ENVIRONMENT="sandbox"
~~~

These names are **examples used by your application**; the SDK does **not** automatically read environment variables. Pass them explicitly to the client.

~~~python
import os
from flutterwave_sdk import FlutterwaveClient

client = FlutterwaveClient(
    client_id=os.environ["FLW_CLIENT_ID"],
    client_secret=os.environ["FLW_CLIENT_SECRET"],
    encryption_key=os.getenv("FLW_ENCRYPTION_KEY"),
    environment=os.getenv("FLW_ENVIRONMENT", "sandbox"),
)
try:
    result = client.banks.list(country="NG")
    print(len(result.data))
finally:
    client.close()
~~~

You can instead supply `access_token="..."` if your application obtains tokens separately. An explicitly provided access token has no known expiry within the SDK; when it stops working, create a client with a fresh token or supply OAuth credentials to permit refresh.

The implementation uses these default API bases:

| Environment | API base |
| --- | --- |
| Sandbox | `https://developersandbox-api.flutterwave.com` |
| Production | `https://f4bexperience.flutterwave.com` |

The default OAuth token URL is `https://idp.flutterwave.com/realms/flutterwave/protocol/openid-connect/token`. Confirm environment and credentials against the [official Flutterwave v4 documentation](https://developer.flutterwave.com/v4/api).

## Quick start

Use a context manager so SDK-created HTTP resources are closed automatically:

~~~python
import os
from flutterwave_sdk import FlutterwaveClient

with FlutterwaveClient(
    client_id=os.environ["FLW_CLIENT_ID"],
    client_secret=os.environ["FLW_CLIENT_SECRET"],
    environment="sandbox",
) as flw:
    banks = flw.banks.list(country="NG")
    for bank in banks:
        print(bank.to_dict())

    created = flw.customers.create(
        email="customer@example.com",
        name={"first": "Ada", "last": "Okafor"},
        phone={"country_code": "234", "number": "8012345678"},
    )
    print(created.status, created.data.id)
~~~

These examples are **API call patterns**, not live-tested end-to-end payments. Use sandbox credentials and the payload fields required by the relevant Flutterwave endpoint. The convenience aliases `flw.customers` and `flw.v4.customers` refer to the same service.

## Service reference

All services below are available under `client.v4` and directly on `client`. Unless stated otherwise, `create`/`retrieve`/`update` operations return `FlutterwaveResponse` and `list` operations return `ListObject`.

| Service | Python access | Implemented methods |
| --- | --- | --- |
| Customers | `client.customers` | `list`, `create`, `retrieve`, `update`, `search` |
| Payment methods | `client.payment_methods` | `list`, `create`, `retrieve` |
| Charges | `client.charges` | `list`, `create`, `retrieve`, `update` |
| Card transactions | `client.card_transactions` | `encrypt_card`, `create_card_payment_method`, `charge`, `direct_charge`, `authorize_pin`, `authorize_otp` |
| Orchestration | `client.orchestration` | `direct_charge`, `order` |
| Banks | `client.banks` | `list`, `branches`, `lookup_account` |
| Mobile networks | `client.mobile_networks` | `list` |
| Virtual accounts | `client.virtual_accounts` | `list`, `create`, `retrieve`, `update` |
| Transfers | `client.transfers` | `list`, `create`, `retrieve`, `update`, `retry_or_duplicate` |
| Transfer recipients | `client.transfers.recipients` | `list`, `create`, `retrieve`, `delete` |
| Transfer senders | `client.transfers.senders` | `list`, `create`, `retrieve`, `delete` |
| Wallets | `client.wallets` | `lookup_account`, `statement`, `balance`, `balances` |
| Refunds | `client.refunds` | `list`, `create`, `retrieve` |
| Settlements | `client.settlements` | `list`, `retrieve` |
| Orders | `client.orders` | generic `list`, `create`, `retrieve`, `update`, `delete` |
| Chargebacks | `client.chargebacks` | generic `list`, `create`, `retrieve`, `update`, `delete` |
| Fees | `client.fees` | generic `list`, `create`, `retrieve`, `update`, `delete` |
| Transactions | `client.transactions` | `retrieve_charge`, `verify_charge`, `verify` |
| Verification | `client.verification` | `retrieve_charge`, `verify_charge` |

**Generic resources:** `orders`, `chargebacks`, and `fees` use `GenericCrudService`. Their presence exposes the generic Python methods; it does **not** mean every HTTP verb is valid for every corresponding Flutterwave endpoint. Check the API reference before calling an operation.

Most mutating methods accept `options=RequestOptions(...)`; some also accept `**extra` or `**params` for endpoint-specific request fields.

## Common workflows

### 1. Create and retrieve a customer

~~~python
customer_response = flw.customers.create(
    email="customer@example.com",
    name={"first": "Ada", "last": "Okafor"},
    meta={"source": "example"},
)
customer_id = str(customer_response.data.id)

customer = flw.customers.retrieve(customer_id)
print(customer.data.to_dict())

customers = flw.customers.list(page=1, size=20)
print(customers.current_page, customers.has_more)
~~~

### 2. Create a payment method and a charge

Create a customer first, then supply a **Flutterwave-supported** payment-method payload. The structure depends on the payment type and country.

~~~python
method = flw.payment_methods.create(
    type="mobile_money",
    customer_id=customer_id,
    mobile_money={
        "country_code": "233",
        "network": "your-supported-network",
        "phone_number": "your-test-number",
    },
)

charge = flw.charges.create(
    amount=100.00,
    currency="GHS",
    reference="order-1001",
    customer_id=customer_id,
    payment_method_id=str(method.data.id),
    redirect_url="https://example.com/payments/return",
)

print(charge.data.to_dict())
~~~

A charge can require customer action or further authorization. **Do not treat a successful API response as proof that funds were collected.** Verify the charge's final status, amount, currency, and reference.

### 3. Orchestrator direct charge

`orchestration.direct_charge` combines customer and payment method details in one endpoint request:

~~~python
response = flw.orchestration.direct_charge(
    amount=100.00,
    currency="GHS",
    reference="order-1002",
    customer={
        "email": "customer@example.com",
        "name": {"first": "Ada", "last": "Okafor"},
    },
    payment_method={
        "type": "mobile_money",
        "mobile_money": {
            "country_code": "233",
            "network": "your-supported-network",
            "phone_number": "your-test-number",
        },
    },
    redirect_url="https://example.com/payments/return",
)
print(response.data.to_dict())
~~~

Refer to Flutterwave's documentation for supported provider codes and any additional fields.

### 4. Banks and account lookup

~~~python
banks = flw.banks.list(country="NG")
branches = flw.banks.branches(country="NG", bank_code="your-bank-code")

account = flw.banks.lookup_account(
    account_number="your-test-account-number",
    account_bank="your-bank-code",
    country="NG",
)
print(account.data.to_dict())
~~~

### 5. Virtual accounts

~~~python
account = flw.virtual_accounts.create(
    reference="va-order-1003",
    customer_id=customer_id,
    amount=2500.00,
    currency="NGN",
    account_type="dynamic",
    narration="Payment for order 1003",
)

account_details = flw.virtual_accounts.retrieve(str(account.data.id))
~~~

`account_type` accepts `"static"` or `"dynamic"`. Identity-verification requirements, supported currencies, and expiry rules depend on the upstream API.

### 6. Transfer recipients and payouts

~~~python
recipient = flw.transfers.recipients.create(
    type="bank",
    bank={
        # Populate the fields required by Flutterwave for your country.
        "account_number": "your-test-account-number",
        "account_bank": "your-bank-code",
    },
)

transfer = flw.transfers.create(
    amount=5000.00,
    currency="NGN",
    recipient_id=str(recipient.data.id),
    reference="payout-1001",
    narration="Vendor payout",
)

status = flw.transfers.retrieve(str(transfer.data.id))
print(status.data.to_dict())
~~~

The SDK also provides `flw.transfers.senders`, transfer listings, updates, and `retry_or_duplicate(transfer_id, ...)`. Payouts may complete asynchronously; reconcile against confirmed provider status before marking them final.

### 7. Wallet balances, refunds, and settlements

~~~python
balance = flw.wallets.balance(currency="NGN")
all_balances = flw.wallets.balances()
statement = flw.wallets.statement(currency="NGN", page=1, size=20)

refund = flw.refunds.create(
    charge_id="your-charge-id",
    amount=100.00,
    reason="Customer requested a refund",
)

settlements = flw.settlements.list(page=1, size=10)
~~~

These requests can affect money or account records. Use test data in the sandbox before invoking live operations.

## Card payments and encryption

The SDK supplies `encrypt_aes_gcm`, `encrypt_card_details`, `encrypt_pin`, and the `client.card_transactions` convenience service. These functions use a **base64-encoded, 32-byte AES-256 key** and a 12-character alphanumeric nonce.

**Before using card helpers with live cardholder data:** Review [Security considerations](#security-considerations). The current multi-field AES-GCM implementation needs a nonce-usage security review and has not been validated here for PCI compliance or production readiness.

### Create an encrypted card payment method

~~~python
import os

encrypted_card = flw.card_transactions.encrypt_card(
    card_number=os.environ["FLW_TEST_CARD_NUMBER"],
    expiry_month=os.environ["FLW_TEST_CARD_MONTH"],
    expiry_year=os.environ["FLW_TEST_CARD_YEAR"],
    cvv=os.environ["FLW_TEST_CARD_CVV"],
)

method = flw.payment_methods.create(
    type="card",
    customer_id=customer_id,
    card=encrypted_card,
)
~~~

The helper reads its encryption key from the client unless one is supplied to the method. **Never log, store, or commit raw PANs, CVVs, PINs, or encryption keys.**

### Compose a customer → card → charge workflow

~~~python
result = flw.card_transactions.charge(
    amount=2500.00,
    currency="NGN",
    reference="card-order-1004",
    customer={"email": "customer@example.com"},
    card_number=os.environ["FLW_TEST_CARD_NUMBER"],
    expiry_month=os.environ["FLW_TEST_CARD_MONTH"],
    expiry_year=os.environ["FLW_TEST_CARD_YEAR"],
    cvv=os.environ["FLW_TEST_CARD_CVV"],
    redirect_url="https://example.com/payments/return",
)

print(result.customer.id)
print(result.payment_method.id)
print(result.charge.id)
# The original HTTP responses are also available:
print(result.charge_response.http_status)
~~~

If you already have a Flutterwave customer ID, supply `customer_id="..."` instead of `customer=...`; the SDK will skip creating a new customer. The multi-step method returns `CardTransactionResult` rather than a single `FlutterwaveResponse`.

For a single orchestrated request, see `flw.card_transactions.direct_charge(...)`.

### Follow-up authorization

If Flutterwave indicates a PIN or OTP challenge, the SDK exposes:

~~~python
pin_result = flw.card_transactions.authorize_pin(
    "your-charge-id",
    pin="test-pin-from-sandbox-flow",
)

otp_result = flw.card_transactions.authorize_otp(
    "your-charge-id",
    otp="test-otp-from-sandbox-flow",
)
~~~

Only perform the authorization step actually requested by the provider. Do not send both unconditionally. These functions submit an update to `/charges/{id}` and do not by themselves establish that payment has succeeded.

## Transaction verification

The verification helpers retrieve `GET /charges/{id}` and compare the returned charge details with expectations supplied by your application.

~~~python
from decimal import Decimal

verified = flw.transactions.verify(
    "your-charge-id",
    expected_reference="order-1001",
    expected_amount=Decimal("2500.00"),
    expected_currency="NGN",
)

if verified.is_trusted_success:
    print("Payment details match the expected successful charge")
else:
    print("Not confirmed:", verified.status, verified.mismatch_reasons)
~~~

`flw.verification.verify_charge(...)` provides the same comparison workflow. The result exposes:

| Property | Meaning |
| --- | --- |
| `response` | Original `FlutterwaveResponse` |
| `charge` / `charge_id` | Returned charge data / requested ID |
| `status` / `is_successful` / `is_failed` | Provider-reported status and categorized flags |
| `reference` / `amount` / `currency` | Parsed charge values |
| `reference_matches` / `amount_matches` / `currency_matches` | Equality checks against your expected values |
| `is_trusted_success` | Success status **and** all *supplied* expectations match |
| `mismatch_reasons` | List of failed checks, e.g. `"amount_mismatch"` |

**Important:** An omitted expected field counts as a passing comparison. Always supply your own order's reference, amount, and currency when deciding whether to fulfil an order. Verification is a snapshot of Flutterwave's response; implement idempotent fulfilment and reconciliation in your application.

## Webhooks

Use `Webhook.construct_event` to check signatures against the **unaltered raw request body** before processing a webhook.

~~~python
import os
from flutterwave_sdk import Webhook
from flutterwave_sdk.webhook import WebhookSignatureError

def handle_flutterwave_webhook(raw_body: bytes, headers: dict[str, str]):
    event = Webhook.construct_event(
        payload=raw_body,
        headers=headers,
        secret_hash=os.environ["FLW_WEBHOOK_SECRET"],
        allow_legacy_verif_hash=False,
    )
    return event
~~~

Your web framework is responsible for retrieving `raw_body` and headers, rejecting invalid requests, and sending the appropriate HTTP response. The helper is **framework-independent**.

The implementation supports:

- `flutterwave-signature`: base64 HMAC-SHA256 over the raw body (default verification scheme).
- `verif-hash`: optional legacy comparison against the configured secret. The default for `construct_event` currently permits this fallback; set `allow_legacy_verif_hash=False` if your integration uses only HMAC signatures.
- `Webhook.verify_signature(...)` for direct verification (with optional `digest="hex"`).
- `Webhook.verify_legacy_verif_hash(...)` for legacy integrations.

Confirm the webhook signature scheme used by **your actual Flutterwave product/version**. Verify the event and then independently verify a payment or payout before altering financial records. Deduplicate webhook deliveries and make handlers idempotent.

## Request options and idempotency

~~~python
from flutterwave_sdk import RequestOptions

options = RequestOptions(
    idempotency_key="order-1001-attempt-0001",
    trace_id="trace-order-1001-0001",
    scenario_key="your-sandbox-scenario",
    headers={"X-Custom-Request-Tag": "checkout"},
)

charge = flw.charges.create(
    amount=100.00,
    currency="NGN",
    reference="order-1001",
    customer_id=customer_id,
    payment_method_id="your-payment-method-id",
    options=options,
)
~~~

| Field | HTTP header | Behavior |
| --- | --- | --- |
| `idempotency_key` | `X-Idempotency-Key` | Required length: 12–255 characters if supplied |
| `trace_id` | `X-Trace-Id` | Required length: 12–255 characters if supplied |
| `scenario_key` | `X-Scenario-Key` | Optional sandbox scenario header |
| `headers` | Custom headers | Additional caller-supplied headers |

Options are applied **per request** rather than stored globally.

The transport retries connection errors and HTTP **409**, **429**, and **5xx** responses up to `max_network_retries` additional attempts, using `Retry-After` if available or exponential backoff with jitter. **Retry behavior is not limited to read-only requests.** For charges, payouts, and other mutations, use provider-supported idempotency keys and reconcile unknown outcomes to avoid duplicate operations.

## Responses and pagination

A successful ordinary request returns a `FlutterwaveResponse`:

~~~python
response = flw.customers.retrieve(customer_id)

print(response.status)       # API payload status (if provided)
print(response.message)      # API payload message (if provided)
print(response.data)         # FlutterwaveObject, list, or scalar
print(response.meta)         # Optional FlutterwaveObject
print(response.http_status)  # HTTP status code
print(response.headers)      # HTTP response headers
print(response.raw)          # Original parsed response mapping
~~~

Response mappings can be accessed by attribute or key, while preserving newly introduced API fields:

~~~python
customer = response.data
print(customer.id)
print(customer["id"])
plain_dict = customer.to_dict()
~~~

List operations return `ListObject` and do not automatically fetch additional pages:

~~~python
page = flw.customers.list(page=1, size=25)
for item in page:
    print(item.to_dict())

print(page.current_page)
print(page.total_pages)
print(page.has_more)
print(page.next_page)

if page.next_page is not None:
    next_page = flw.customers.list(page=page.next_page, size=25)
~~~

Pagination helpers expect metadata shaped like `meta.page_info.current_page` and `meta.page_info.total_pages`. If the API omits those fields, the helper cannot infer further pages.

## Error handling

~~~python
from flutterwave_sdk import (
    APIConnectionError,
    APIError,
    AuthenticationError,
    FlutterwaveError,
    RateLimitError,
)
from flutterwave_sdk.errors import NotFoundError

try:
    response = flw.customers.retrieve("customer-id")
except AuthenticationError:
    # Check client credentials / token configuration.
    raise
except RateLimitError as exc:
    print("Rate limited:", exc.http_status, exc.headers)
except NotFoundError:
    print("Customer not found")
except APIConnectionError as exc:
    print("Transport failure:", exc)
except APIError as exc:
    print(exc.http_status, exc.code, exc.error_type, exc.response)
except FlutterwaveError as exc:
    print("SDK error:", exc)
~~~

| Exception | Condition |
| --- | --- |
| `BadRequestError` | HTTP 400 |
| `AuthenticationError` | HTTP 401 or OAuth token failure |
| `PermissionError` | HTTP 403 (the SDK class, not Python's built-in) |
| `NotFoundError` | HTTP 404; import from `flutterwave_sdk.errors` |
| `ConflictError` | HTTP 409 after retries |
| `RateLimitError` | HTTP 429 after retries |
| `APIError` | Other unsuccessful HTTP responses |
| `APIConnectionError` | HTTP connection/transport failures |
| `InvalidRequestOptionsError` | Invalid idempotency/trace header length |
| `EncryptionError` | Invalid card encryption input |
| `WebhookSignatureError` | Invalid signature or non-JSON event after signature verification |

All SDK API exceptions derive from `FlutterwaveError`. The standard fields are `message`, `http_status`, `code`, `error_type`, `response`, and `headers` when available.

## Custom requests and environments

### Call an unwrapped endpoint

~~~python
response = flw.request_raw(
    "GET",
    "/some-supported-v4-resource",
    params={"page": 1},
)
~~~

Use paths relative to the configured API base. `request_raw` uses the same token manager, headers, retry behavior, error handling, and response conversion as the service methods. It is not a promise that a specified path exists.

### Inject your own HTTP client

~~~python
import httpx
from flutterwave_sdk import FlutterwaveClient
from flutterwave_sdk.http import Environment

with httpx.Client(timeout=15.0) as transport:
    with FlutterwaveClient(
        client_id="your-client-id",
        client_secret="your-client-secret",
        environment=Environment(
            name="sandbox",
            api_base="https://developersandbox-api.flutterwave.com",
        ),
        http_client=transport,
        max_network_retries=1,
    ) as flw:
        page = flw.customers.list()
~~~

When supplied with an external `httpx.Client`, the SDK does **not** own or close it. Use the transport's own context manager or lifecycle management.

## Security considerations

Payment integrations require additional safeguards beyond successful API calls:

1. **Keep credentials server-side.** Do not embed OAuth secrets, bearer tokens, webhook secrets, encryption keys, raw card details, or PINs in browser/mobile builds, commits, logs, or analytics.
2. **Review card encryption before production.** The current `encrypt_card_details` encrypts multiple fields using the **same AES-GCM nonce and key**, which is a security concern for GCM. Its protocol compatibility and nonce handling must be audited and corrected as appropriate before processing live cardholder data.
3. **Check PCI DSS scope.** Receiving PAN/CVV on your own backend can expand compliance obligations. Prefer Flutterwave-hosted or appropriately tokenized payment flows where possible.
4. **Protect against duplicate transactions.** Mutating requests can be retried; use unique business references, appropriate idempotency keys, and provider-side reconciliation.
5. **Verify every financial outcome.** Compare transaction status, reference, amount, and currency with your server-side order before granting value or marking a payout settled.
6. **Verify webhooks using raw bytes.** Apply the signature scheme appropriate to your Flutterwave integration, deduplicate events, and never rely solely on a callback or redirect.
7. **Separate sandbox from production.** Use independent credentials and configuration; avoid accidental live transactions during development.

This repository's source has not been represented here as independently penetration-tested, PCI-certified, or production-audited.

## Project structure

~~~text
flutterwave_sdk/
├── __init__.py           # Public exports
├── _version.py            # SDK version
├── auth.py                # OAuth token acquisition and caching
├── client.py              # FlutterwaveClient and service binding
├── http.py                # HTTP transport and environments
├── errors.py              # SDK and API exception hierarchy
├── objects.py             # Responses, dynamic objects, list helpers
├── request_options.py     # Idempotency and tracing headers
├── params.py              # Typed request payload definitions
├── encryption.py          # Card / PIN encryption utilities
├── webhook.py             # Webhook signature and event helpers
├── _util.py               # Request payload utilities
├── services/
│   ├── base.py
│   ├── banks.py
│   ├── card_transactions.py
│   ├── charges.py
│   ├── customers.py
│   ├── generic.py
│   ├── mobile_networks.py
│   ├── orchestration.py
│   ├── payment_methods.py
│   ├── refunds.py
│   ├── settlements.py
│   ├── transfers.py
│   ├── verification.py
│   ├── virtual_accounts.py
│   └── wallets.py
├── pyproject.toml         # Project metadata and dependencies
├── uv.lock                # Locked dependency graph
├── .python-version        # Requested Python version
└── py.typed               # Marker for typed-package consumers
~~~

## Current limitations

As of the repository snapshot used to prepare this documentation:

- **No conventional distribution configuration:** the repository is not yet structured/configured as a typical installable `flutterwave_sdk` wheel, and no published release is verified.
- **No automated test suite or CI workflow is present** in the current tracked tree. Code examples are based on source inspection, not successful sandbox integration tests.
- **Synchronous API only:** the client uses `httpx.Client`; there is no `AsyncClient` or async service interface.
- **Partial type coverage:** selected request payloads are typed, but service responses are intentionally dynamic.
- **No automatic pagination:** follow pages explicitly through `ListObject`.
- **No built-in webhook server or persistence layer.** Applications implement HTTP endpoints, deduplication, state transitions, and reconciliation.
- **Generic wrappers are not endpoint-specific contracts.** Available HTTP verbs must be checked against the Flutterwave API reference.
- **Card encryption needs security review**, especially AES-GCM nonce reuse, before live card processing.

These are current codebase constraints, not features promised for a future release.

## Development and contributing

The project currently uses `uv` for dependency locking.

~~~bash
git clone https://github.com/Leydotpy/flutterwave_sdk.git
cd flutterwave_sdk
uv sync
~~~

A helpful contribution should include a description of the endpoint or issue, minimal reproduction steps, any relevant Flutterwave v4 API reference, and tests that mock outbound HTTP requests. Avoid including real customer data or live credentials in issues and pull requests.

Suggested areas for improvement include packaging, automated tests/CI, encryption security review, per-method retry policies, expanded type annotations, and documentation-backed coverage of v4 endpoints.

Open an issue or pull request at [Leydotpy/flutterwave_sdk](https://github.com/Leydotpy/flutterwave_sdk).

### License

No license file was present in the inspected repository snapshot. Until a license is explicitly added, **do not assume open-source redistribution or modification permissions beyond those granted by applicable law or the repository owner**.

## Further reading

- [Flutterwave v4 API reference](https://developer.flutterwave.com/v4/api)
- [Flutterwave developer documentation](https://developer.flutterwave.com/v4/docs)
- [Flutterwave v4 encryption guide](https://developer.flutterwave.com/v4.0.0/docs/encryption)
- [Flutterwave webhook documentation](https://developer.flutterwave.com/docs/webhooks)
- [uv documentation](https://docs.astral.sh/uv/)

---

**Maintainer:** [Leydotpy](https://github.com/Leydotpy) · **Repository:** [flutterwave_sdk](https://github.com/Leydotpy/flutterwave_sdk) · **SDK version:** `0.1.0`

*Flutterwave is a trademark of its respective owner. This repository is an independent integration project.*
