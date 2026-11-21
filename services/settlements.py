from __future__ import annotations

from typing import Any

from ..objects import FlutterwaveResponse, ListObject
from ..request_options import RequestOptions
from .base import APIService


class SettlementService(APIService):
    def list(self, *, page: int = 1, size: int = 10, options: RequestOptions | None = None) -> ListObject[Any]:
        response = self._get("/settlements", params={"page": page, "size": size}, options=options)
        return self._list_object(response)

    def retrieve(self, settlement_id: str, *, options: RequestOptions | None = None) -> FlutterwaveResponse:
        return self._get(f"/settlements/{settlement_id}", options=options)
