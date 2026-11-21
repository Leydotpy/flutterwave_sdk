from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from ..encryption import encrypt_card_details, encrypt_pin
from ..objects import FlutterwaveObject, FlutterwaveResponse
from ..request_options import RequestOptions
from .charges import ChargeService
from .customers import CustomerService
from .orchestration import OrchestrationService
from .payment_methods import PaymentMethodService


@dataclass(frozen=True, slots=True)
class CardTransactionResult:
    """Result of the multi-step general card flow."""

    customer: FlutterwaveObject
    payment_method: FlutterwaveObject
    charge: FlutterwaveObject
    customer_response: FlutterwaveResponse
    payment_method_response: FlutterwaveResponse
    charge_response: FlutterwaveResponse


class CardTransactionService:
    """Convenience service for card transactions.

    The underlying Flutterwave v4 model is still customer -> card payment method -> charge.
    This service only composes those primitive resources into a developer-friendly workflow.
    """

    def __init__(
        self,
        *,
        customers: CustomerService,
        payment_methods: PaymentMethodService,
        charges: ChargeService,
        orchestration: OrchestrationService,
        encryption_key: str | None = None,
    ) -> None:
        self._customers = customers
        self._payment_methods = payment_methods
        self._charges = charges
        self._orchestration = orchestration
        self._encryption_key = encryption_key

    def encrypt_card(
        self,
        *,
        card_number: str,
        expiry_month: str | int,
        expiry_year: str | int,
        cvv: str,
        encryption_key: str | None = None,
        nonce: str | None = None,
    ) -> dict[str, str]:
        return encrypt_card_details(
            card_number=card_number,
            expiry_month=expiry_month,
            expiry_year=expiry_year,
            cvv=cvv,
            encryption_key=self._resolve_encryption_key(encryption_key),
            nonce=nonce,
        )

    def create_card_payment_method(
        self,
        *,
        customer_id: str,
        card_number: str,
        expiry_month: str | int,
        expiry_year: str | int,
        cvv: str,
        encryption_key: str | None = None,
        nonce: str | None = None,
        meta: Mapping[str, Any] | None = None,
        options: RequestOptions | None = None,
    ) -> FlutterwaveResponse:
        encrypted_card = self.encrypt_card(
            card_number=card_number,
            expiry_month=expiry_month,
            expiry_year=expiry_year,
            cvv=cvv,
            encryption_key=encryption_key,
            nonce=nonce,
        )
        return self._payment_methods.create(
            type="card",
            customer_id=customer_id,
            card=encrypted_card,
            meta=meta,
            options=options,
        )

    def charge(
        self,
        *,
        amount: float,
        currency: str,
        reference: str,
        card_number: str,
        expiry_month: str | int,
        expiry_year: str | int,
        cvv: str,
        customer_id: str | None = None,
        customer: Mapping[str, Any] | None = None,
        redirect_url: str | None = None,
        description: str | None = None,
        meta: Mapping[str, Any] | None = None,
        encryption_key: str | None = None,
        customer_options: RequestOptions | None = None,
        payment_method_options: RequestOptions | None = None,
        charge_options: RequestOptions | None = None,
    ) -> CardTransactionResult:
        """Create/reuse a customer, create an encrypted card payment method, then charge it."""

        if not customer_id and not customer:
            raise ValueError("Either customer_id or customer must be supplied.")

        if customer_id:
            # We avoid fetching the customer here so the helper remains cheap and deterministic.
            customer_response = FlutterwaveResponse(
                status="success",
                message="Existing customer supplied by caller.",
                data=FlutterwaveObject.construct_from({"id": customer_id}),
                meta=None,
                raw={"data": {"id": customer_id}},
                http_status=200,
                headers={},
            )
            customer_obj = customer_response.data
        else:
            assert customer is not None
            customer_response = self._customers.create(options=customer_options, **dict(customer))
            customer_obj = customer_response.data
            customer_id = str(customer_obj.id)

        payment_method_response = self.create_card_payment_method(
            customer_id=customer_id,
            card_number=card_number,
            expiry_month=expiry_month,
            expiry_year=expiry_year,
            cvv=cvv,
            encryption_key=encryption_key,
            options=payment_method_options,
        )
        payment_method_obj = payment_method_response.data

        charge_response = self._charges.create(
            amount=amount,
            currency=currency,
            reference=reference,
            customer_id=customer_id,
            payment_method_id=str(payment_method_obj.id),
            redirect_url=redirect_url,
            description=description,
            meta=meta,
            options=charge_options,
        )

        return CardTransactionResult(
            customer=customer_obj,
            payment_method=payment_method_obj,
            charge=charge_response.data,
            customer_response=customer_response,
            payment_method_response=payment_method_response,
            charge_response=charge_response,
        )

    def direct_charge(
        self,
        *,
        amount: float,
        currency: str,
        reference: str,
        customer: Mapping[str, Any],
        card_number: str,
        expiry_month: str | int,
        expiry_year: str | int,
        cvv: str,
        redirect_url: str | None = None,
        description: str | None = None,
        meta: Mapping[str, Any] | None = None,
        encryption_key: str | None = None,
        options: RequestOptions | None = None,
        **extra: Any,
    ) -> FlutterwaveResponse:
        """Use Flutterwave's orchestrator flow with encrypted card details."""

        encrypted_card = self.encrypt_card(
            card_number=card_number,
            expiry_month=expiry_month,
            expiry_year=expiry_year,
            cvv=cvv,
            encryption_key=encryption_key,
        )
        return self._orchestration.direct_charge(
            amount=amount,
            currency=currency,
            reference=reference,
            customer=dict(customer),
            payment_method={"type": "card", "card": encrypted_card},
            redirect_url=redirect_url,
            description=description,
            meta=meta,
            options=options,
            **extra,
        )

    def authorize_pin(
        self,
        charge_id: str,
        *,
        pin: str,
        encryption_key: str | None = None,
        nonce: str | None = None,
        options: RequestOptions | None = None,
    ) -> FlutterwaveResponse:
        encrypted_pin = encrypt_pin(
            pin=pin,
            encryption_key=self._resolve_encryption_key(encryption_key),
            nonce=nonce,
        )
        return self._charges.update(
            charge_id,
            authorization={"type": "pin", "pin": encrypted_pin},
            options=options,
        )

    def authorize_otp(
        self,
        charge_id: str,
        *,
        otp: str,
        options: RequestOptions | None = None,
    ) -> FlutterwaveResponse:
        return self._charges.update(
            charge_id,
            authorization={"type": "otp", "otp": {"code": otp}},
            options=options,
        )

    def _resolve_encryption_key(self, encryption_key: str | None) -> str:
        key = encryption_key or self._encryption_key
        if not key:
            raise ValueError(
                "An encryption key is required. Pass encryption_key=... to FlutterwaveClient "
                "or to this method."
            )
        return key
