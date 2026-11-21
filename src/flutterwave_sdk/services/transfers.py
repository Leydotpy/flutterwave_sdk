from __future__ import annotations

from typing import Any, Mapping

from ..objects import FlutterwaveResponse, ListObject
from ..request_options import RequestOptions
from .base import APIService


class TransferRecipientService(APIService):
    def list(
        self,
        *,
        page: int = 1,
        size: int = 10,
        options: RequestOptions | None = None,
    ) -> ListObject[Any]:
        response = self._get("/transfers/recipients", params={"page": page, "size": size}, options=options)
        return self._list_object(response)

    def create(
        self,
        *,
        type: str,
        bank: Mapping[str, Any] | None = None,
        mobile_money: Mapping[str, Any] | None = None,
        wallet: Mapping[str, Any] | None = None,
        meta: Mapping[str, Any] | None = None,
        options: RequestOptions | None = None,
        **extra: Any,
    ) -> FlutterwaveResponse:
        body: dict[str, Any] = {
            "type": type,
            "bank": dict(bank) if bank else None,
            "mobile_money": dict(mobile_money) if mobile_money else None,
            "wallet": dict(wallet) if wallet else None,
            "meta": dict(meta) if meta is not None else None,
        }
        body.update(extra)
        return self._post("/transfers/recipients", body=body, options=options)

    def retrieve(self, recipient_id: str, *, options: RequestOptions | None = None) -> FlutterwaveResponse:
        return self._get(f"/transfers/recipients/{recipient_id}", options=options)

    def delete(self, recipient_id: str, *, options: RequestOptions | None = None) -> FlutterwaveResponse:
        return self._delete(f"/transfers/recipients/{recipient_id}", options=options)


class TransferSenderService(APIService):
    def list(self, *, page: int = 1, size: int = 10, options: RequestOptions | None = None) -> ListObject[Any]:
        response = self._get("/transfers/senders", params={"page": page, "size": size}, options=options)
        return self._list_object(response)

    def create(self, *, options: RequestOptions | None = None, **params: Any) -> FlutterwaveResponse:
        return self._post("/transfers/senders", body=params, options=options)

    def retrieve(self, sender_id: str, *, options: RequestOptions | None = None) -> FlutterwaveResponse:
        return self._get(f"/transfers/senders/{sender_id}", options=options)

    def delete(self, sender_id: str, *, options: RequestOptions | None = None) -> FlutterwaveResponse:
        return self._delete(f"/transfers/senders/{sender_id}", options=options)


class TransferService(APIService):
    def __init__(self, api_client: Any) -> None:
        super().__init__(api_client)
        self.recipients = TransferRecipientService(api_client)
        self.senders = TransferSenderService(api_client)

    def list(
        self,
        *,
        page: int = 1,
        size: int = 10,
        status: str | None = None,
        reference: str | None = None,
        options: RequestOptions | None = None,
    ) -> ListObject[Any]:
        response = self._get(
            "/transfers",
            params={"page": page, "size": size, "status": status, "reference": reference},
            options=options,
        )
        return self._list_object(response)

    def create(
        self,
        *,
        amount: float,
        currency: str,
        recipient_id: str,
        reference: str,
        action: str = "instant",
        narration: str | None = None,
        meta: Mapping[str, Any] | None = None,
        options: RequestOptions | None = None,
        **extra: Any,
    ) -> FlutterwaveResponse:
        body: dict[str, Any] = {
            "action": action,
            "amount": amount,
            "currency": currency,
            "recipient_id": recipient_id,
            "reference": reference,
            "narration": narration,
            "meta": dict(meta) if meta is not None else None,
        }
        body.update(extra)
        return self._post("/transfers", body=body, options=options)

    def retrieve(self, transfer_id: str, *, options: RequestOptions | None = None) -> FlutterwaveResponse:
        return self._get(f"/transfers/{transfer_id}", options=options)

    def update(
        self,
        transfer_id: str,
        *,
        options: RequestOptions | None = None,
        **params: Any,
    ) -> FlutterwaveResponse:
        return self._put(f"/transfers/{transfer_id}", body=params, options=options)

    def retry_or_duplicate(
        self,
        transfer_id: str,
        *,
        options: RequestOptions | None = None,
        **params: Any,
    ) -> FlutterwaveResponse:
        return self._post(f"/transfers/{transfer_id}/retries", body=params, options=options)
