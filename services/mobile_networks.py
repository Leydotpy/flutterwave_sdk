from __future__ import annotations

from typing import Any

from ..objects import ListObject
from ..request_options import RequestOptions
from .base import APIService


class MobileNetworkService(APIService):
    def list(
        self,
        *,
        country: str,
        options: RequestOptions | None = None,
    ) -> ListObject[Any]:
        response = self._get("/mobile-networks", params={"country": country}, options=options)
        return self._list_object(response)
