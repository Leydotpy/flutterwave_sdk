from __future__ import annotations

from typing import Any, Mapping

from ..objects import FlutterwaveResponse, ListObject
from ..request_options import RequestOptions
from .base import APIService


class GenericCrudService(APIService):
    """Escape hatch for v4 resources not yet wrapped with first-class methods."""

    def __init__(self, api_client: Any, resource_path: str) -> None:
        super().__init__(api_client)
        self.resource_path = resource_path.rstrip("/")

    def list(self, *, page: int = 1, size: int = 10, options: RequestOptions | None = None, **params: Any) -> ListObject[Any]:
        query = {"page": page, "size": size, **params}
        response = self._get(self.resource_path, params=query, options=options)
        return self._list_object(response)

    def create(self, *, options: RequestOptions | None = None, **params: Any) -> FlutterwaveResponse:
        return self._post(self.resource_path, body=params, options=options)

    def retrieve(self, resource_id: str, *, options: RequestOptions | None = None) -> FlutterwaveResponse:
        return self._get(f"{self.resource_path}/{resource_id}", options=options)

    def update(self, resource_id: str, *, options: RequestOptions | None = None, **params: Any) -> FlutterwaveResponse:
        return self._put(f"{self.resource_path}/{resource_id}", body=params, options=options)

    def delete(self, resource_id: str, *, options: RequestOptions | None = None) -> FlutterwaveResponse:
        return self._delete(f"{self.resource_path}/{resource_id}", options=options)
