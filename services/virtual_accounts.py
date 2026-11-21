from __future__ import annotations

from typing import Any, Literal, Mapping

from ..objects import FlutterwaveResponse, ListObject
from ..request_options import RequestOptions
from .base import APIService


class VirtualAccountService(APIService):
    def list(
        self,
        *,
        page: int = 1,
        size: int = 10,
        customer_id: str | None = None,
        options: RequestOptions | None = None,
    ) -> ListObject[Any]:
        response = self._get(
            "/virtual-accounts",
            params={"page": page, "size": size, "customer_id": customer_id},
            options=options,
        )
        return self._list_object(response)

    def create(
        self,
        *,
        reference: str,
        customer_id: str,
        amount: float,
        currency: str,
        account_type: Literal["static", "dynamic"],
        narration: str | None = None,
        expiry: int | None = None,
        bvn: str | None = None,
        nin: str | None = None,
        meta: Mapping[str, Any] | None = None,
        options: RequestOptions | None = None,
        **extra: Any,
    ) -> FlutterwaveResponse:
        body: dict[str, Any] = {
            "reference": reference,
            "customer_id": customer_id,
            "amount": amount,
            "currency": currency,
            "account_type": account_type,
            "narration": narration,
            "expiry": expiry,
            "bvn": bvn,
            "nin": nin,
            "meta": dict(meta) if meta is not None else None,
        }
        body.update(extra)
        return self._post("/virtual-accounts", body=body, options=options)

    def retrieve(
        self,
        virtual_account_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> FlutterwaveResponse:
        return self._get(f"/virtual-accounts/{virtual_account_id}", options=options)

    def update(
        self,
        virtual_account_id: str,
        *,
        options: RequestOptions | None = None,
        **params: Any,
    ) -> FlutterwaveResponse:
        return self._put(f"/virtual-accounts/{virtual_account_id}", body=params, options=options)
