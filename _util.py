from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def remove_none(value: Any) -> Any:
    """Recursively remove None values from API request bodies."""
    if isinstance(value, Mapping):
        return {k: remove_none(v) for k, v in value.items() if v is not None}
    if isinstance(value, list):
        return [remove_none(v) for v in value]
    if isinstance(value, tuple):
        return tuple(remove_none(v) for v in value)
    return value


def merge_dicts(*items: Mapping[str, Any] | None) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for item in items:
        if item:
            merged.update(item)
    return merged
