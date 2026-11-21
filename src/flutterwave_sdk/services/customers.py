from __future__ import annotations

from typing import Any, Mapping

from ..objects import FlutterwaveResponse, ListObject
from ..params import AddressParam, CustomerCreateParams, NameParam, PhoneParam
from ..request_options import RequestOptions
from .base import APIService


class CustomerService(APIService):
    def list(
        self,
        *,
        page: int = 1,
        size: int = 10,
        options: RequestOptions | None = None,
    ) -> ListObject[Any]:
        response = self._get("/customers", params={"page": page, "size": size}, options=options)
        return self._list_object(response)

    def create(
        self,
        *,
        email: str,
        name: NameParam | None = None,
        phone: PhoneParam | None = None,
        address: AddressParam | None = None,
        meta: Mapping[str, Any] | None = None,
        options: RequestOptions | None = None,
        **extra: Any,
    ) -> FlutterwaveResponse:
        body: CustomerCreateParams = {
            "email": email,
            "name": name,  # type: ignore[typeddict-item]
            "phone": phone,  # type: ignore[typeddict-item]
            "address": address,  # type: ignore[typeddict-item]
            "meta": dict(meta or {}),
        }
        body.update(extra)
        return self._post("/customers", body=body, options=options)

    def retrieve(self, customer_id: str, *, options: RequestOptions | None = None) -> FlutterwaveResponse:
        return self._get(f"/customers/{customer_id}", options=options)

    def update(
        self,
        customer_id: str,
        *,
        email: str | None = None,
        name: NameParam | None = None,
        phone: PhoneParam | None = None,
        address: AddressParam | None = None,
        meta: Mapping[str, Any] | None = None,
        options: RequestOptions | None = None,
        **extra: Any,
    ) -> FlutterwaveResponse:
        body: dict[str, Any] = {
            "email": email,
            "name": name,
            "phone": phone,
            "address": address,
            "meta": dict(meta) if meta is not None else None,
        }
        body.update(extra)
        return self._put(f"/customers/{customer_id}", body=body, options=options)

    def search(
        self,
        *,
        query: Mapping[str, Any],
        options: RequestOptions | None = None,
    ) -> ListObject[Any]:
        response = self._post("/customers/search", body=dict(query), options=options)
        return self._list_object(response)
