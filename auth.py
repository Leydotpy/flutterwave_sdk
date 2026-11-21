from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Mapping

import httpx

from .errors import APIConnectionError, AuthenticationError

TOKEN_URL = "https://idp.flutterwave.com/realms/flutterwave/protocol/openid-connect/token"


@dataclass(slots=True)
class AccessToken:
    value: str
    expires_at: float | None = None
    token_type: str = "Bearer"

    def is_valid(self, *, leeway_seconds: int = 60) -> bool:
        if not self.value:
            return False
        if self.expires_at is None:
            return True
        return time.time() < (self.expires_at - leeway_seconds)


class OAuthTokenManager:
    """Small OAuth2 client-credentials token cache for Flutterwave v4."""

    def __init__(
        self,
        *,
        client_id: str | None,
        client_secret: str | None,
        token_url: str = TOKEN_URL,
        http_client: httpx.Client | None = None,
        access_token: str | None = None,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self._http_client = http_client or httpx.Client(timeout=30)
        self._owns_http_client = http_client is None
        self._token = AccessToken(access_token) if access_token else None

    def get_token(self) -> str:
        if self._token and self._token.is_valid():
            return self._token.value
        return self.refresh_token().value

    def refresh_token(self) -> AccessToken:
        if not self.client_id or not self.client_secret:
            raise AuthenticationError(
                "client_id and client_secret are required to generate a Flutterwave access token"
            )
        try:
            response = self._http_client.post(
                self.token_url,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "client_credentials",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        except httpx.HTTPError as exc:
            raise APIConnectionError("Unable to connect to Flutterwave token endpoint") from exc

        try:
            payload: Mapping[str, Any] = response.json()
        except ValueError as exc:
            raise AuthenticationError(
                "Flutterwave token endpoint returned a non-JSON response",
                http_status=response.status_code,
                headers=response.headers,
            ) from exc

        if response.status_code >= 400 or not payload.get("access_token"):
            raise AuthenticationError(
                str(payload.get("error_description") or payload.get("error") or "Token request failed"),
                http_status=response.status_code,
                response=payload,
                headers=response.headers,
            )

        expires_in = int(payload.get("expires_in") or 0)
        self._token = AccessToken(
            value=str(payload["access_token"]),
            expires_at=time.time() + expires_in if expires_in else None,
            token_type=str(payload.get("token_type") or "Bearer"),
        )
        return self._token

    def close(self) -> None:
        if self._owns_http_client:
            self._http_client.close()
