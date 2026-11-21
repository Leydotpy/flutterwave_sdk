from __future__ import annotations

from typing import Any, Mapping

from .._util import remove_none
from ..http import APIClient
from ..objects import FlutterwaveResponse, ListObject
from ..request_options import RequestOptions


class APIService:
    def __init__(self, api_client: APIClient) -> None:
        self._api_client = api_client

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        body: Mapping[str, Any] | None = None,
        options: RequestOptions | None = None,
    ) -> FlutterwaveResponse:
        return self._api_client.request(
            method,
            path,
            params=remove_none(params) if params else None,
            json=remove_none(body) if body else None,
            options=options,
        )

    def _get(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        options: RequestOptions | None = None,
    ) -> FlutterwaveResponse:
        return self._request("GET", path, params=params, options=options)

    def _post(
        self,
        path: str,
        *,
        body: Mapping[str, Any] | None = None,
        options: RequestOptions | None = None,
    ) -> FlutterwaveResponse:
        return self._request("POST", path, body=body, options=options)

    def _put(
        self,
        path: str,
        *,
        body: Mapping[str, Any] | None = None,
        options: RequestOptions | None = None,
    ) -> FlutterwaveResponse:
        return self._request("PUT", path, body=body, options=options)

    def _delete(
        self,
        path: str,
        *,
        options: RequestOptions | None = None,
    ) -> FlutterwaveResponse:
        return self._request("DELETE", path, options=options)

    def _list_object(self, response: FlutterwaveResponse) -> ListObject[Any]:
        data = response.data if isinstance(response.data, list) else []
        return ListObject(data=data, meta=response.meta, response=response)
