from __future__ import annotations

from typing import Any, Mapping

from ..objects import FlutterwaveResponse, ListObject
from ..params import PaymentMethodType
from ..request_options import RequestOptions
from .base import APIService


class PaymentMethodService(APIService):
    def list(
        self,
        *,
        page: int = 1,
        size: int = 10,
        customer_id: str | None = None,
        type: PaymentMethodType | None = None,
        options: RequestOptions | None = None,
    ) -> ListObject[Any]:
        response = self._get(
            "/payment-methods",
            params={"page": page, "size": size, "customer_id": customer_id, "type": type},
            options=options,
        )
        return self._list_object(response)

    def create(
        self,
        *,
        type: PaymentMethodType,
        customer_id: str | None = None,
        card: Mapping[str, Any] | None = None,
        mobile_money: Mapping[str, Any] | None = None,
        ussd: Mapping[str, Any] | None = None,
        opay: Mapping[str, Any] | None = None,
        bank_account: Mapping[str, Any] | None = None,
        bank_transfer: Mapping[str, Any] | None = None,
        meta: Mapping[str, Any] | None = None,
        options: RequestOptions | None = None,
        **extra: Any,
    ) -> FlutterwaveResponse:
        body: dict[str, Any] = {
            "type": type,
            "customer_id": customer_id,
            "card": dict(card) if card else None,
            "mobile_money": dict(mobile_money) if mobile_money else None,
            "ussd": dict(ussd) if ussd else None,
            "opay": dict(opay) if opay else None,
            "bank_account": dict(bank_account) if bank_account else None,
            "bank_transfer": dict(bank_transfer) if bank_transfer else None,
            "meta": dict(meta) if meta is not None else None,
        }
        body.update(extra)
        return self._post("/payment-methods", body=body, options=options)

    def retrieve(
        self,
        payment_method_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> FlutterwaveResponse:
        return self._get(f"/payment-methods/{payment_method_id}", options=options)
