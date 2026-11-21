from __future__ import annotations

from typing import Any, Mapping

from ..objects import FlutterwaveResponse, ListObject
from ..request_options import RequestOptions
from .base import APIService


class ChargeService(APIService):
    def list(
        self,
        *,
        page: int = 1,
        size: int = 10,
        customer_id: str | None = None,
        virtual_account_id: str | None = None,
        reference: str | None = None,
        status: str | None = None,
        options: RequestOptions | None = None,
    ) -> ListObject[Any]:
        response = self._get(
            "/charges",
            params={
                "page": page,
                "size": size,
                "customer_id": customer_id,
                "virtual_account_id": virtual_account_id,
                "reference": reference,
                "status": status,
            },
            options=options,
        )
        return self._list_object(response)

    def create(
        self,
        *,
        amount: float,
        currency: str,
        reference: str,
        customer_id: str,
        payment_method_id: str,
        redirect_url: str | None = None,
        authorization: Mapping[str, Any] | None = None,
        description: str | None = None,
        meta: Mapping[str, Any] | None = None,
        options: RequestOptions | None = None,
        **extra: Any,
    ) -> FlutterwaveResponse:
        body: dict[str, Any] = {
            "amount": amount,
            "currency": currency,
            "reference": reference,
            "customer_id": customer_id,
            "payment_method_id": payment_method_id,
            "redirect_url": redirect_url,
            "authorization": dict(authorization) if authorization else None,
            "description": description,
            "meta": dict(meta) if meta is not None else None,
        }
        body.update(extra)
        return self._post("/charges", body=body, options=options)

    def retrieve(self, charge_id: str, *, options: RequestOptions | None = None) -> FlutterwaveResponse:
        return self._get(f"/charges/{charge_id}", options=options)

    def update(
        self,
        charge_id: str,
        *,
        options: RequestOptions | None = None,
        **params: Any,
    ) -> FlutterwaveResponse:
        return self._put(f"/charges/{charge_id}", body=params, options=options)
