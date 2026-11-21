from __future__ import annotations

from typing import Any, Mapping

from ..objects import FlutterwaveResponse, ListObject
from ..request_options import RequestOptions
from .base import APIService


class RefundService(APIService):
    def list(self, *, page: int = 1, size: int = 10, options: RequestOptions | None = None) -> ListObject[Any]:
        response = self._get("/refunds", params={"page": page, "size": size}, options=options)
        return self._list_object(response)

    def create(
        self,
        *,
        charge_id: str,
        amount: float | None = None,
        reason: str | None = None,
        meta: Mapping[str, Any] | None = None,
        options: RequestOptions | None = None,
        **extra: Any,
    ) -> FlutterwaveResponse:
        body: dict[str, Any] = {
            "charge_id": charge_id,
            "amount": amount,
            "reason": reason,
            "meta": dict(meta) if meta is not None else None,
        }
        body.update(extra)
        return self._post("/refunds", body=body, options=options)

    def retrieve(self, refund_id: str, *, options: RequestOptions | None = None) -> FlutterwaveResponse:
        return self._get(f"/refunds/{refund_id}", options=options)
