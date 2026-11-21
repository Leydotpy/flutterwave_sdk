from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Mapping

from .errors import InvalidRequestOptionsError


@dataclass(frozen=True, slots=True)
class RequestOptions:
    """Per-request transport metadata, similar in spirit to Stripe's request options.

    Use this for idempotency, trace correlation, sandbox scenario simulation, and custom headers.
    """

    idempotency_key: str | None = None
    trace_id: str | None = None
    scenario_key: str | None = None
    headers: Mapping[str, str] = field(default_factory=dict)

    def to_headers(self) -> dict[str, str]:
        headers: dict[str, str] = dict(self.headers)
        if self.idempotency_key:
            _validate_header_length("X-Idempotency-Key", self.idempotency_key)
            if not re.fullmatch(r"[A-Za-z0-9]+", self.idempotency_key):
                raise InvalidRequestOptionsError("X-Idempotency-Key must be alphanumeric")
            headers["X-Idempotency-Key"] = self.idempotency_key
        if self.trace_id:
            _validate_header_length("X-Trace-Id", self.trace_id)
            headers["X-Trace-Id"] = self.trace_id
        if self.scenario_key:
            headers["X-Scenario-Key"] = self.scenario_key
        return headers


def _validate_header_length(name: str, value: str) -> None:
    if not 12 <= len(value) <= 255:
        raise InvalidRequestOptionsError(f"{name} must be between 12 and 255 characters long")
