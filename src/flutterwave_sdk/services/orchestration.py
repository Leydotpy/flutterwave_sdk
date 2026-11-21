from __future__ import annotations

from typing import Any, Mapping

from ..objects import FlutterwaveResponse
from ..request_options import RequestOptions
from .base import APIService


class OrchestrationService(APIService):
    def direct_charge(
        self,
        *,
        amount: float,
        currency: str,
        reference: str,
        customer: Mapping[str, Any],
        payment_method: Mapping[str, Any],
        redirect_url: str | None = None,
        authorization: Mapping[str, Any] | None = None,
        merchant_vat_amount: float | None = None,
        meta: Mapping[str, Any] | None = None,
        options: RequestOptions | None = None,
        **extra: Any,
    ) -> FlutterwaveResponse:
        body: dict[str, Any] = {
            "amount": amount,
            "currency": currency,
            "reference": reference,
            "customer": dict(customer),
            "payment_method": dict(payment_method),
            "redirect_url": redirect_url,
            "authorization": dict(authorization) if authorization else None,
            "merchant_vat_amount": merchant_vat_amount,
            "meta": dict(meta) if meta is not None else None,
        }
        body.update(extra)
        return self._post("/orchestration/direct-charges", body=body, options=options)

    def order(
        self,
        *,
        amount: float,
        currency: str,
        reference: str,
        customer: Mapping[str, Any],
        payment_method: Mapping[str, Any],
        redirect_url: str | None = None,
        meta: Mapping[str, Any] | None = None,
        options: RequestOptions | None = None,
        **extra: Any,
    ) -> FlutterwaveResponse:
        body: dict[str, Any] = {
            "amount": amount,
            "currency": currency,
            "reference": reference,
            "customer": dict(customer),
            "payment_method": dict(payment_method),
            "redirect_url": redirect_url,
            "meta": dict(meta) if meta is not None else None,
        }
        body.update(extra)
        return self._post("/orchestration/orders", body=body, options=options)
