from __future__ import annotations

from typing import Any, Mapping

from ..objects import FlutterwaveResponse, ListObject
from ..request_options import RequestOptions
from .base import APIService


class BankService(APIService):
    def list(
        self,
        *,
        country: str,
        options: RequestOptions | None = None,
    ) -> ListObject[Any]:
        response = self._get("/banks", params={"country": country}, options=options)
        return self._list_object(response)

    def branches(
        self,
        *,
        bank_id: str | None = None,
        bank_code: str | None = None,
        country: str | None = None,
        options: RequestOptions | None = None,
    ) -> ListObject[Any]:
        response = self._get(
            "/banks/branches",
            params={"bank_id": bank_id, "bank_code": bank_code, "country": country},
            options=options,
        )
        return self._list_object(response)

    def lookup_account(
        self,
        *,
        account_number: str,
        account_bank: str,
        country: str | None = None,
        options: RequestOptions | None = None,
        **extra: Any,
    ) -> FlutterwaveResponse:
        body: dict[str, Any] = {
            "account_number": account_number,
            "account_bank": account_bank,
            "country": country,
        }
        body.update(extra)
        return self._post("/banks/account-lookup", body=body, options=options)
