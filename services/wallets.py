from __future__ import annotations

from typing import Any

from ..objects import FlutterwaveResponse, ListObject
from ..request_options import RequestOptions
from .base import APIService


class WalletService(APIService):
    def lookup_account(self, *, account_number: str, currency: str, options: RequestOptions | None = None, **extra: Any) -> FlutterwaveResponse:
        body = {"account_number": account_number, "currency": currency, **extra}
        return self._post("/wallets/account-lookup", body=body, options=options)

    def statement(
        self,
        *,
        currency: str,
        page: int = 1,
        size: int = 10,
        options: RequestOptions | None = None,
    ) -> ListObject[Any]:
        response = self._get(
            "/wallets/statement",
            params={"currency": currency, "page": page, "size": size},
            options=options,
        )
        return self._list_object(response)

    def balance(self, *, currency: str, options: RequestOptions | None = None) -> FlutterwaveResponse:
        return self._get(f"/wallets/balances/{currency}", options=options)

    def balances(self, *, options: RequestOptions | None = None) -> FlutterwaveResponse:
        return self._get("/wallets/balances", options=options)
