from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from .base import APIService
from ..objects import FlutterwaveObject, FlutterwaveResponse
from ..request_options import RequestOptions

SUCCESSFUL_STATUSES = {"successful", "success", "succeeded", "completed"}
FAILED_STATUSES = {"failed", "declined", "cancelled", "canceled"}


@dataclass(slots=True)
class TransactionVerificationResult:
    response: FlutterwaveResponse
    charge: FlutterwaveObject
    charge_id: str
    status: str
    reference: str | None
    amount: Decimal | None
    currency: str | None
    expected_reference: str | None = None
    expected_amount: Decimal | None = None
    expected_currency: str | None = None

    @property
    def is_successful(self) -> bool:
        return self.status.lower() in SUCCESSFUL_STATUSES

    @property
    def is_failed(self) -> bool:
        return self.status.lower() in FAILED_STATUSES

    @property
    def reference_matches(self) -> bool:
        return self.expected_reference is None or self.reference == self.expected_reference

    @property
    def amount_matches(self) -> bool:
        return self.expected_amount is None or self.amount == self.expected_amount

    @property
    def currency_matches(self) -> bool:
        return (
                self.expected_currency is None
                or (self.currency or "").upper() == self.expected_currency.upper()
        )

    @property
    def is_trusted_success(self) -> bool:
        return (
                self.is_successful
                and self.reference_matches
                and self.amount_matches
                and self.currency_matches
        )

    @property
    def mismatch_reasons(self) -> list[str]:
        reasons: list[str] = []

        if not self.reference_matches:
            reasons.append("reference_mismatch")

        if not self.amount_matches:
            reasons.append("amount_mismatch")

        if not self.currency_matches:
            reasons.append("currency_mismatch")

        return reasons


class TransactionVerificationService(APIService):
    def retrieve_charge(
            self,
            charge_id: str,
            *,
            options: RequestOptions | None = None,
    ) -> FlutterwaveResponse:
        return self._get(f"/charges/{charge_id}", options=options)

    def verify_charge(
            self,
            charge_id: str,
            *,
            expected_reference: str | None = None,
            expected_amount: Decimal | int | float | str | None = None,
            expected_currency: str | None = None,
            options: RequestOptions | None = None,
    ) -> TransactionVerificationResult:
        response = self.retrieve_charge(charge_id, options=options)

        charge = response.data
        if not isinstance(charge, FlutterwaveObject):
            charge = FlutterwaveObject.construct_from({})

        return TransactionVerificationResult(
            response=response,
            charge=charge,
            charge_id=charge_id,
            status=str(charge.get("status") or ""),
            reference=str(charge.get("reference") or charge.get("tx_ref") or "") or None,
            amount=_decimal_or_none(charge.get("amount")),
            currency=str(charge.get("currency") or "") or None,
            expected_reference=expected_reference,
            expected_amount=_decimal_or_none(expected_amount),
            expected_currency=expected_currency,
        )


class TransactionService(TransactionVerificationService):
    def verify(
            self,
            charge_id: str,
            *,
            expected_reference: str | None = None,
            expected_amount: Decimal | int | float | str | None = None,
            expected_currency: str | None = None,
            options: RequestOptions | None = None,
    ) -> TransactionVerificationResult:
        return self.verify_charge(
            charge_id,
            expected_reference=expected_reference,
            expected_amount=expected_amount,
            expected_currency=expected_currency,
            options=options,
        )


def _decimal_or_none(value: object) -> Decimal | None:
    if value is None:
        return None

    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
