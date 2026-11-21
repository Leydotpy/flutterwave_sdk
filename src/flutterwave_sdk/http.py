from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Any, Mapping

import httpx
import simplejson as json_codec

from ._version import __version__
from .auth import OAuthTokenManager
from .errors import APIConnectionError, error_from_response
from .objects import FlutterwaveResponse
from .request_options import RequestOptions


@dataclass(frozen=True, slots=True)
class Environment:
    name: str
    api_base: str


SANDBOX = Environment("sandbox", "https://developersandbox-api.flutterwave.com")
PRODUCTION = Environment("production", "https://f4bexperience.flutterwave.com")


def resolve_environment(value: str | Environment) -> Environment:
    if isinstance(value, Environment):
        return value
    normalized = value.lower().strip()
    if normalized in {"sandbox", "test", "development", "dev"}:
        return SANDBOX
    if normalized in {"production", "prod", "live"}:
        return PRODUCTION
    raise ValueError("environment must be 'sandbox' or 'production'")


class APIClient:
    """Low-level HTTP transport with auth, retries, errors and response coercion."""

    def __init__(
        self,
        *,
        token_manager: OAuthTokenManager,
        environment: str | Environment = "sandbox",
        http_client: httpx.Client | None = None,
        timeout: float = 30.0,
        max_network_retries: int = 2,
    ) -> None:
        self.environment = resolve_environment(environment)
        self.token_manager = token_manager
        self.max_network_retries = max_network_retries
        self._http_client = http_client or httpx.Client(timeout=timeout)
        self._owns_http_client = http_client is None

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Mapping[str, Any] | None = None,
        options: RequestOptions | None = None,
    ) -> FlutterwaveResponse:
        url = self._url(path)
        request_options = options or RequestOptions()
        headers = self._headers(request_options)
        last_exc: httpx.HTTPError | None = None

        for attempt in range(self.max_network_retries + 1):
            try:
                response = self._http_client.request(
                    method,
                    url,
                    params=params,
                    content=json_codec.dumps(json, use_decimal=True) if json is not None else None,
                    headers=headers,
                )
            except httpx.HTTPError as exc:
                last_exc = exc
                if attempt < self.max_network_retries and self._retry_permitted(method, request_options):
                    self._sleep_before_retry(attempt)
                    continue
                raise APIConnectionError("Unable to connect to Flutterwave API") from exc

            if self._should_retry(response, attempt) and self._retry_permitted(method, request_options):
                self._sleep_before_retry(attempt, response=response)
                continue

            return self._handle_response(response)

        raise APIConnectionError("Unable to connect to Flutterwave API") from last_exc

    def close(self) -> None:
        if self._owns_http_client:
            self._http_client.close()
        self.token_manager.close()

    def _url(self, path: str) -> str:
        normalized = path if path.startswith("/") else f"/{path}"
        return f"{self.environment.api_base.rstrip('/')}{normalized}"

    def _headers(self, options: RequestOptions) -> dict[str, str]:
        token = self.token_manager.get_token()
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "User-Agent": f"flutterwave-sdk-python/{__version__}",
        }
        headers.update(options.to_headers())
        return headers

    def _handle_response(self, response: httpx.Response) -> FlutterwaveResponse:
        try:
            payload = response.json()
        except ValueError:
            payload = {"message": response.text}

        if response.status_code >= 400:
            raise error_from_response(response.status_code, payload, response.headers)
        if not isinstance(payload, Mapping):
            payload = {"status": None, "message": None, "data": payload}
        return FlutterwaveResponse.from_payload(
            payload,
            http_status=response.status_code,
            headers=response.headers,
        )

    def _should_retry(self, response: httpx.Response, attempt: int) -> bool:
        if attempt >= self.max_network_retries:
            return False
        if response.status_code in {409, 429}:
            return True
        return 500 <= response.status_code < 600

    @staticmethod
    def _retry_permitted(method: str, options: RequestOptions) -> bool:
        return method.upper() in {"GET", "HEAD", "OPTIONS"} or bool(options.idempotency_key)

    def _sleep_before_retry(self, attempt: int, response: httpx.Response | None = None) -> None:
        retry_after = None
        if response is not None:
            retry_after_header = response.headers.get("Retry-After")
            if retry_after_header:
                try:
                    retry_after = float(retry_after_header)
                except ValueError:
                    retry_after = None
        delay = retry_after if retry_after is not None else min(0.5 * (2**attempt), 4.0)
        delay += random.random() * 0.1
        time.sleep(delay)
